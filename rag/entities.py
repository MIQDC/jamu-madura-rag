import os
import re
import pickle

import numpy as np
import tensorflow as tf


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "model_bilstm_s5.keras"
)

CONFIG_PATH = os.path.join(
    BASE_DIR,
    "models",
    "query_model_config_s5.pkl"
)


# ============================================================
# TOKENIZATION
# Mengikuti preprocessing eksperimen:
# re.findall(r'\b\w+\b', text.lower())
# ============================================================

def tokenize_text(text):
    text = str(text).lower()
    return re.findall(r"\b\w+\b", text)


# ============================================================
# LOAD CONFIG
# ============================================================

with open(CONFIG_PATH, "rb") as f:
    QUERY_CONFIG = pickle.load(f)


word_to_index = QUERY_CONFIG["word_to_index"]
label_to_index = QUERY_CONFIG["label_to_index"]
MAX_LEN = int(QUERY_CONFIG["MAX_LEN"])


# Inverse label mapping
index_to_label = {
    int(index): label
    for label, index in label_to_index.items()
}


# ============================================================
# VOCABULARY
#
# Jangan menentukan ukuran vocabulary secara manual.
# Gunakan index maksimum yang memang tersimpan di config.
# ============================================================

VOCAB_SIZE = max(word_to_index.values()) + 1

PAD_INDEX = word_to_index.get("<PAD>", 0)

UNK_INDEX = word_to_index.get("<UNK>")

if UNK_INDEX is None:
    raise ValueError(
        "Token <UNK> tidak ditemukan dalam word_to_index."
    )


# ============================================================
# BUILD BI-LSTM
# Arsitektur mengikuti model penelitian final.
# ============================================================

def build_bilstm_model():

    model = tf.keras.Sequential([
        tf.keras.Input(
            shape=(MAX_LEN,),
            dtype="int32"
        ),

        tf.keras.layers.Embedding(
            input_dim=VOCAB_SIZE,
            output_dim=100,
            mask_zero=True
        ),

        tf.keras.layers.Bidirectional(
            tf.keras.layers.LSTM(
                128,
                return_sequences=True
            )
        ),

        tf.keras.layers.Dropout(0.2),

        tf.keras.layers.Dense(
            len(label_to_index),
            activation="softmax"
        )
    ])

    model.build(
        input_shape=(None, MAX_LEN)
    )

    return model


# ============================================================
# LOAD MODEL
# ============================================================

bilstm_model = build_bilstm_model()

bilstm_model.load_weights(MODEL_PATH)


# ============================================================
# CONVERT TOKEN -> INDEX
# ============================================================

def tokens_to_indices(tokens):
    """
    Mengubah token hasil tokenisasi menjadi index vocabulary.
    Token yang tidak ditemukan menggunakan <UNK>.
    """

    indices = []

    for token in tokens:

        index = word_to_index.get(
            token,
            UNK_INDEX
        )

        indices.append(index)

    return indices


# ============================================================
# PAD / TRUNCATE
# ============================================================

def prepare_sequence(tokens):
    """
    Membentuk sequence dengan panjang MAX_LEN.
    Padding dilakukan di belakang (post-padding).
    """

    indices = tokens_to_indices(tokens)

    # Truncate
    indices = indices[:MAX_LEN]

    # Post padding
    if len(indices) < MAX_LEN:
        indices += [
            PAD_INDEX
        ] * (
            MAX_LEN - len(indices)
        )

    return np.array(
        indices,
        dtype=np.int32
    )

def normalize_query_for_entities(text):
    """
    Menghapus instruksi tambahan yang berada setelah
    inti pertanyaan, khusus untuk ekstraksi entitas.
    Teks query asli tetap dipertahankan untuk RAG.
    """
    text = str(text).strip()

    instruction_patterns = [
        r"\s*[,;.!?]?\s*jelaskan\s+khasiat\b.*$",
        r"\s*[,;.!?]?\s*jelaskan\s+aturan\s+minum\b.*$",
        r"\s*[,;.!?]?\s*berdasarkan\s+data\b.*$",
    ]

    for pattern in instruction_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    return text.strip()

# ============================================================
# EXTRACT ENTITY
# ============================================================


def extract_entities(text):
    """
    Menjalankan Bi-LSTM untuk mengenali entitas:

    B-BAHAN
    I-BAHAN
    B-KHASIAT
    I-KHASIAT

    Return:
    {
        "tokens": [...],
        "labels": [...],
        "bahan": [...],
        "khasiat": [...]
    }
    """

    # --------------------------------------------------------
    # Tokenization
    # --------------------------------------------------------

    normalized_text = normalize_query_for_entities(text)
    tokens = tokenize_text(normalized_text)

    if len(tokens) == 0:

        return {
            "tokens": [],
            "labels": [],
            "bahan": [],
            "khasiat": []
        }


    # --------------------------------------------------------
    # Prepare sequence
    # --------------------------------------------------------

    sequence = prepare_sequence(tokens)

    X = np.expand_dims(
        sequence,
        axis=0
    )


    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    prediction = bilstm_model.predict(
        X,
        verbose=0
    )

    predicted_indices = np.argmax(
        prediction[0],
        axis=-1
    )


    # --------------------------------------------------------
    # Decode labels
    # --------------------------------------------------------

    predicted_labels = []

    for i, token in enumerate(tokens):

        label_index = int(
            predicted_indices[i]
        )

        label = index_to_label.get(
            label_index,
            "O"
        )

        predicted_labels.append(label)


    # --------------------------------------------------------
    # Extract entity spans
    # --------------------------------------------------------

    bahan_entities = []
    khasiat_entities = []

    current_tokens = []
    current_type = None


    def finish_current_entity():

        nonlocal current_tokens
        nonlocal current_type

        if not current_tokens:
            return

        entity = " ".join(
            current_tokens
        )

        if current_type == "BAHAN":
            bahan_entities.append(entity)

        elif current_type == "KHASIAT":
            khasiat_entities.append(entity)

        current_tokens = []
        current_type = None


    # --------------------------------------------------------
    # BIO parsing
    # --------------------------------------------------------

    for token, label in zip(
        tokens,
        predicted_labels
    ):

        # ----------------------------------------------------
        # B-BAHAN
        # ----------------------------------------------------

        if label == "B-BAHAN":

            finish_current_entity()

            current_tokens = [
                token
            ]

            current_type = "BAHAN"


        # ----------------------------------------------------
        # I-BAHAN
        # ----------------------------------------------------

        elif label == "I-BAHAN":

            if current_type == "BAHAN":

                current_tokens.append(
                    token
                )

            else:

                finish_current_entity()

                current_tokens = [
                    token
                ]

                current_type = "BAHAN"


        # ----------------------------------------------------
        # B-KHASIAT
        # ----------------------------------------------------

        elif label == "B-KHASIAT":

            finish_current_entity()

            current_tokens = [
                token
            ]

            current_type = "KHASIAT"


        # ----------------------------------------------------
        # I-KHASIAT
        # ----------------------------------------------------

        elif label == "I-KHASIAT":

            if current_type == "KHASIAT":

                current_tokens.append(
                    token
                )

            else:

                finish_current_entity()

                current_tokens = [
                    token
                ]

                current_type = "KHASIAT"


        # ----------------------------------------------------
        # O
        # ----------------------------------------------------

        else:

            finish_current_entity()


    # Selesaikan entity terakhir
    finish_current_entity()


    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "tokens": tokens,
        "labels": predicted_labels,
        "bahan": bahan_entities,
        "khasiat": khasiat_entities
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    test_query = (
        "jamu apa yang mengandung jahe "
        "untuk menambah nafsu makan"
    )

    result = extract_entities(
        test_query
    )

    print("=" * 70)
    print("TEST ENTITY EXTRACTION")
    print("=" * 70)

    print("\nQuery:")
    print(test_query)

    print("\nTokens:")
    print(result["tokens"])

    print("\nBIO:")
    for token, label in zip(
        result["tokens"],
        result["labels"]
    ):
        print(
            f"{token:25s} -> {label}"
        )

    print("\nBAHAN:")
    print(result["bahan"])

    print("\nKHASIAT:")
    print(result["khasiat"])