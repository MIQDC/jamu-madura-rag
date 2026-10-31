import os
import pickle
import re

import faiss
import numpy as np
import pandas as pd
from gensim.models import Word2Vec

try:
    from .entities import extract_entities
except ImportError:
    from entities import extract_entities


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "df_clean.csv"
)

WORD2VEC_PATH = os.path.join(
    BASE_DIR,
    "models",
    "w2v_query_model_revised.model"
)

FAISS_INDEX_PATH = os.path.join(
    BASE_DIR,
    "faiss",
    "faiss_index_final.index"
)

FAISS_MAPPING_PATH = os.path.join(
    BASE_DIR,
    "faiss",
    "faiss_to_id_final.pkl"
)


# ============================================================
# KONFIGURASI RETRIEVAL
# ============================================================

TOP_K_CANDIDATE = 20
TOP_K_FINAL = 5


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_PATH)


# ============================================================
# LOAD WORD2VEC
# ============================================================

w2v_model = Word2Vec.load(
    WORD2VEC_PATH
)


# ============================================================
# LOAD FAISS
# ============================================================

faiss_index = faiss.read_index(
    FAISS_INDEX_PATH
)


# ============================================================
# LOAD FAISS MAPPING
#
# Bentuk mapping pada checkpoint:
# FAISS index 0 -> ID_JAMU 1
# FAISS index 1 -> ID_JAMU 2
# dst.
# ============================================================

with open(
    FAISS_MAPPING_PATH,
    "rb"
) as f:

    faiss_to_id = pickle.load(f)


# ============================================================
# NORMALISASI TEXT
# ============================================================

def normalize_entity_match_text(text):
    """
    Normalisasi teks untuk entity matching.

    Langkah:
    1. lower-case
    2. punctuation -> spasi
    3. hapus spasi berlebih
    """

    text = str(text).lower().strip()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# ENTITY MATCHING SCORE
# ============================================================

def entity_match_score(
    row,
    bahan_entities,
    khasiat_entities
):
    """
    Menghitung jumlah entity yang cocok terhadap dokumen.

    BAHAN    -> field KANDUNGAN
    KHASIAT  -> field KHASIAT

    Return:
    matched_entity
    total_entity
    entity_ratio
    """

    kandungan = normalize_entity_match_text(
        row["KANDUNGAN"]
    )

    khasiat = normalize_entity_match_text(
        row["KHASIAT"]
    )

    total_entity = (
        len(bahan_entities)
        + len(khasiat_entities)
    )

    matched_entity = 0


    # --------------------------------------------------------
    # BAHAN
    # --------------------------------------------------------

    for entity in bahan_entities:

        normalized_entity = (
            normalize_entity_match_text(entity)
        )

        if (
            normalized_entity
            and normalized_entity in kandungan
        ):
            matched_entity += 1


    # --------------------------------------------------------
    # KHASIAT
    # --------------------------------------------------------

    for entity in khasiat_entities:

        normalized_entity = (
            normalize_entity_match_text(entity)
        )

        if (
            normalized_entity
            and normalized_entity in khasiat
        ):
            matched_entity += 1


    # --------------------------------------------------------
    # RATIO
    # --------------------------------------------------------

    if total_entity > 0:

        entity_ratio = (
            matched_entity
            / total_entity
        )

    else:

        entity_ratio = 0.0


    return (
        matched_entity,
        total_entity,
        entity_ratio
    )


# ============================================================
# WORD2VEC QUERY VECTOR
# ============================================================

def entities_to_query_vector(
    bahan_entities,
    khasiat_entities
):
    """
    Membentuk query vector dari token-token entity
    menggunakan Word2Vec.

    Vector akhir = mean pooling
    kemudian L2 normalization.
    """

    entity_texts = (
        bahan_entities
        + khasiat_entities
    )

    vectors = []


    for entity in entity_texts:

        tokens = re.findall(
            r"\b\w+\b",
            str(entity).lower()
        )

        for token in tokens:

            if token in w2v_model.wv:

                vectors.append(
                    w2v_model.wv[token]
                )


    # --------------------------------------------------------
    # Tidak ada vector
    # --------------------------------------------------------

    if len(vectors) == 0:

        return None


    # --------------------------------------------------------
    # Mean pooling
    # --------------------------------------------------------

    query_vector = np.mean(
        np.asarray(
            vectors,
            dtype=np.float32
        ),
        axis=0
    )


    # --------------------------------------------------------
    # L2 normalization
    # --------------------------------------------------------

    norm = np.linalg.norm(
        query_vector
    )

    if norm == 0:

        return None


    query_vector = (
        query_vector
        / norm
    )


    return query_vector.astype(
        np.float32
    )


# ============================================================
# GET DOCUMENT BY ID
# ============================================================

def get_document_by_id(
    jamu_id
):
    """
    Mengambil satu dokumen berdasarkan ID_JAMU.
    """

    result = df[
        df["ID_JAMU"] == int(jamu_id)
    ]

    if result.empty:

        return None

    return result.iloc[0]


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_baseline(
    query,
    top_k_candidate=TOP_K_CANDIDATE,
    top_k_final=TOP_K_FINAL
):
    """
    Pipeline retrieval:

    1. Extract entity dengan Bi-LSTM
    2. Bentuk query vector dengan Word2Vec
    3. FAISS Top-K candidate
    4. Entity-aware reranking
    5. Ambil final Top-K
    """

    # ========================================================
    # 1. EXTRACT ENTITY
    # ========================================================

    entity_result = extract_entities(
        query
    )

    bahan_entities = entity_result[
        "bahan"
    ]

    khasiat_entities = entity_result[
        "khasiat"
    ]


    # ========================================================
    # 2. QUERY VECTOR
    # ========================================================

    query_vector = (
        entities_to_query_vector(
            bahan_entities,
            khasiat_entities
        )
    )


    # ========================================================
    # FALLBACK
    # ========================================================

    if query_vector is None:

        return {
            "query": query,
            "bahan": bahan_entities,
            "khasiat": khasiat_entities,
            "results": [],
            "message": (
                "Tidak ditemukan representasi "
                "Word2Vec untuk entitas query."
            )
        }


    # ========================================================
    # 3. FAISS SEARCH
    # ========================================================

    query_vector_2d = np.expand_dims(
        query_vector,
        axis=0
    )

    similarities, indices = (
        faiss_index.search(
            query_vector_2d,
            top_k_candidate
        )
    )


    similarities = similarities[0]
    indices = indices[0]


    # ========================================================
    # 4. ENTITY-AWARE RERANKING
    # ========================================================

    candidates = []


    for similarity, faiss_idx in zip(
        similarities,
        indices
    ):

        # ----------------------------------------------------
        # Valid FAISS index
        # ----------------------------------------------------

        if faiss_idx < 0:

            continue


        # ----------------------------------------------------
        # FAISS index -> ID_JAMU
        # ----------------------------------------------------

        jamu_id = faiss_to_id[
            int(faiss_idx)
        ]


        # ----------------------------------------------------
        # Get document
        # ----------------------------------------------------

        row = get_document_by_id(
            jamu_id
        )

        if row is None:

            continue


        # ----------------------------------------------------
        # Entity matching
        # ----------------------------------------------------

        (
            matched_entity,
            total_entity,
            entity_ratio
        ) = entity_match_score(
            row,
            bahan_entities,
            khasiat_entities
        )


        # ----------------------------------------------------
        # Save candidate
        # ----------------------------------------------------

        candidates.append({
            "id_jamu": int(jamu_id),
            "semantic_similarity": float(
                similarity
            ),
            "matched_entity": int(
                matched_entity
            ),
            "total_entity": int(
                total_entity
            ),
            "entity_ratio": float(
                entity_ratio
            )
        })


    # ========================================================
    # 5. RERANKING
    #
    # Prioritas:
    # 1. jumlah entity cocok
    # 2. semantic similarity
    # ========================================================

    candidates.sort(
        key=lambda x: (
            x["matched_entity"],
            x["semantic_similarity"]
        ),
        reverse=True
    )


    # ========================================================
    # 6. FINAL TOP-K
    # ========================================================

    final_results = []


    for rank, candidate in enumerate(
        candidates[:top_k_final],
        start=1
    ):

        jamu_id = candidate[
            "id_jamu"
        ]

        row = get_document_by_id(
            jamu_id
        )


        result = {
            "rank": rank,
            "id_jamu": jamu_id,
            "nama_jamu": row[
                "NAMA JAMU"
            ],
            "khasiat": row[
                "KHASIAT"
            ],
            "kandungan": row[
                "KANDUNGAN"
            ],
            "aturan_minum": row[
                "ATURAN MINUM"
            ],
            "efek_samping": row[
                "EFEK SAMPING"
            ],
            "jenis": row[
                "JENIS"
            ],
            "produsen": row[
                "PRODUSEN"
            ],
            "kategori": row[
                "KATEGORI"
            ],
            "lokasi_pemasaran": row[
                "LOKASI PEMASARAN"
            ],
            "lokasi_produksi": row[
                "LOKASI PRODUKSI"
            ],
            "kabupaten": row[
                "KABUPATEN"
            ],
            "perizinan": row[
                "PERIZINAN"
            ],
            "semantic_similarity": candidate[
                "semantic_similarity"
            ],
            "matched_entity": candidate[
                "matched_entity"
            ],
            "total_entity": candidate[
                "total_entity"
            ],
            "entity_ratio": candidate[
                "entity_ratio"
            ]
        }

        final_results.append(
            result
        )


    # ========================================================
    # RETURN
    # ========================================================

    return {
        "query": query,
        "bahan": bahan_entities,
        "khasiat": khasiat_entities,
        "results": final_results,
        "message": None
    }



def retrieve(
    query,
    top_k_candidate=TOP_K_CANDIDATE,
    top_k_final=TOP_K_FINAL
):
    """
    Hybrid retrieval:
    1. Ekstraksi entitas Bi-LSTM.
    2. Kandidat semantik dari FAISS.
    3. Kandidat tambahan melalui pencocokan entitas langsung.
    4. Deduplikasi dan entity-aware reranking.
    5. Mengembalikan Top-K dengan struktur respons API yang sama.
    """
    entity_result = extract_entities(query)
    bahan_entities = entity_result["bahan"]
    khasiat_entities = entity_result["khasiat"]

    query_vector = entities_to_query_vector(
        bahan_entities,
        khasiat_entities
    )

    semantic_scores = {}

    if query_vector is not None:
        k = min(int(top_k_candidate), int(faiss_index.ntotal))

        if k > 0:
            similarities, indices = faiss_index.search(
                np.expand_dims(query_vector, axis=0).astype(np.float32),
                k
            )

            for similarity, faiss_idx in zip(similarities[0], indices[0]):
                if faiss_idx < 0:
                    continue

                jamu_id = int(faiss_to_id[int(faiss_idx)])
                semantic_scores[jamu_id] = float(similarity)

    candidates = {}

    # Kandidat dari FAISS: pertahankan skor semantik asli.
    for jamu_id, similarity in semantic_scores.items():
        row = get_document_by_id(jamu_id)
        if row is None:
            continue

        matched, total, ratio = entity_match_score(
            row, bahan_entities, khasiat_entities
        )

        candidates[jamu_id] = {
            "id_jamu": int(jamu_id),
            "semantic_similarity": float(similarity),
            "matched_entity": int(matched),
            "total_entity": int(total),
            "entity_ratio": float(ratio)
        }

    # Kandidat langsung: tambahkan jika minimal satu entitas cocok.
    for _, row in df.iterrows():
        jamu_id = int(row["ID_JAMU"])

        if jamu_id in candidates:
            continue

        matched, total, ratio = entity_match_score(
            row, bahan_entities, khasiat_entities
        )

        if matched <= 0:
            continue

        candidates[jamu_id] = {
            "id_jamu": jamu_id,
            "semantic_similarity": 0.0,
            "matched_entity": int(matched),
            "total_entity": int(total),
            "entity_ratio": float(ratio)
        }

    ranked = sorted(
        candidates.values(),
        key=lambda item: (
            item["matched_entity"],
            item["semantic_similarity"]
        ),
        reverse=True
    )

    final_results = []

    for rank, candidate in enumerate(ranked[:top_k_final], start=1):
        jamu_id = candidate["id_jamu"]
        row = get_document_by_id(jamu_id)

        if row is None:
            continue

        final_results.append({
            "rank": rank,
            "id_jamu": jamu_id,
            "nama_jamu": row["NAMA JAMU"],
            "khasiat": row["KHASIAT"],
            "kandungan": row["KANDUNGAN"],
            "aturan_minum": row["ATURAN MINUM"],
            "efek_samping": row["EFEK SAMPING"],
            "jenis": row["JENIS"],
            "produsen": row["PRODUSEN"],
            "kategori": row["KATEGORI"],
            "lokasi_pemasaran": row["LOKASI PEMASARAN"],
            "lokasi_produksi": row["LOKASI PRODUKSI"],
            "kabupaten": row["KABUPATEN"],
            "perizinan": row["PERIZINAN"],
            "semantic_similarity": candidate["semantic_similarity"],
            "matched_entity": candidate["matched_entity"],
            "total_entity": candidate["total_entity"],
            "entity_ratio": candidate["entity_ratio"]
        })

    # Perbarui rank jika ada dokumen yang dilewati.
    for rank, item in enumerate(final_results, start=1):
        item["rank"] = rank

    return {
        "query": query,
        "bahan": bahan_entities,
        "khasiat": khasiat_entities,
        "results": final_results,
        "message": None
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    test_query = (
        "jamu apa yang mengandung jahe "
        "untuk menambah nafsu makan"
    )


    result = retrieve(
        test_query
    )


    print("=" * 80)
    print("TEST RETRIEVAL")
    print("=" * 80)

    print("\nQuery:")
    print(result["query"])

    print("\nBAHAN:")
    print(result["bahan"])

    print("\nKHASIAT:")
    print(result["khasiat"])


    print("\n" + "-" * 80)
    print("HASIL FINAL TOP-5")
    print("-" * 80)


    for item in result["results"]:

        print(
            f"\nRank {item['rank']}"
        )

        print(
            f"ID Jamu           : "
            f"{item['id_jamu']}"
        )

        print(
            f"Nama Jamu         : "
            f"{item['nama_jamu']}"
        )

        print(
            f"Semantic Similarity: "
            f"{item['semantic_similarity']:.6f}"
        )

        print(
            f"Entity Match      : "
            f"{item['matched_entity']}/"
            f"{item['total_entity']}"
        )

        print(
            f"Entity Ratio      : "
            f"{item['entity_ratio']:.2f}"
        )

        print(
            f"Kandungan         : "
            f"{item['kandungan']}"
        )

        print(
            f"Khasiat           : "
            f"{item['khasiat']}"
        )