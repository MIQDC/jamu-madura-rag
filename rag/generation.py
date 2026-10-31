import os
import time

import requests
from dotenv import load_dotenv

try:
    from .retrieval import retrieve
except ImportError:
    from retrieval import retrieve


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ENV_PATH)


# ============================================================
# GEMINI CONFIG
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = "gemini-3.8-flash"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)


# ============================================================
# VALIDASI API KEY
# ============================================================

if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY belum ditemukan. "
        "Periksa file .env."
    )


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(results):
    """
    Mengubah hasil retrieval menjadi context
    untuk Gemini.
    """

    context_parts = []

    for item in results:

        context = (
            f"DOKUMEN {item['rank']}\n"
            f"ID JAMU: {item['id_jamu']}\n"
            f"NAMA JAMU: {item['nama_jamu']}\n"
            f"KHASIAT: {item['khasiat']}\n"
            f"KANDUNGAN: {item['kandungan']}\n"
            f"ATURAN MINUM: {item['aturan_minum']}\n"
            f"EFEK SAMPING: {item['efek_samping']}\n"
            f"JENIS: {item['jenis']}\n"
            f"PRODUSEN: {item['produsen']}\n"
            f"KATEGORI: {item['kategori']}\n"
            f"LOKASI PEMASARAN: {item['lokasi_pemasaran']}\n"
            f"LOKASI PRODUKSI: {item['lokasi_produksi']}\n"
            f"KABUPATEN: {item['kabupaten']}\n"
            f"PERIZINAN: {item['perizinan']}\n"
        )

        context_parts.append(
            context
        )

    return "\n".join(
        context_parts
    )


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(
    query,
    bahan,
    khasiat,
    results
):
    """
    Membuat prompt RAG.
    Gemini hanya bertugas membuat jawaban naratif singkat.
    Detail rekomendasi ditampilkan oleh aplikasi.
    """

    context = build_context(
        results
    )

    bahan_text = (
        ", ".join(bahan)
        if bahan
        else "tidak terdeteksi"
    )

    khasiat_text = (
        ", ".join(khasiat)
        if khasiat
        else "tidak terdeteksi"
    )

    prompt = f"""
Anda adalah generator jawaban pada sistem
tanya jawab Jamu Tradisional Madura.

Jawab pertanyaan pengguna hanya berdasarkan
CONTEXT KNOWLEDGE BASE.

Pertanyaan pengguna:
{query}

Entitas BAHAN:
{bahan_text}

Entitas KHASIAT:
{khasiat_text}

CONTEXT KNOWLEDGE BASE:
{context}

Tugas Anda adalah membuat jawaban naratif singkat
untuk bagian "Jawaban RAG".

Aturan:
- Jawab langsung pertanyaan pengguna.
- Gunakan hanya informasi yang ada pada context.
- Jangan menggunakan pengetahuan dari luar context.
- Jangan membuat daftar nama jamu.
- Jangan menghitung jumlah rekomendasi.
- Jangan mengulang detail setiap dokumen.
- Jangan membahas produsen, bentuk produk, lokasi, atau atribut
  lain yang tidak diperlukan untuk menjawab pertanyaan,
  kecuali atribut tersebut memang ditanyakan pengguna.
- Jangan membuat klaim bahwa jamu pasti menyembuhkan penyakit.
- Jangan menggunakan Markdown.
- Jangan menggunakan heading.
- Jangan menggunakan bullet.
- Jangan menggunakan simbol **, ###, atau ---.
- Tulis hanya 2 atau 3 kalimat.
- Kalimat pertama harus menjawab langsung pertanyaan pengguna.
- Kalimat kedua dapat menjelaskan bahwa hasil yang sesuai
  ditampilkan pada bagian rekomendasi.
- Pastikan kalimat terakhir selesai dan diakhiri tanda baca.

Contoh gaya jawaban:
"Berdasarkan informasi pada knowledge base, terdapat data jamu
yang mengandung bahan yang ditanyakan dan memiliki informasi
khasiat yang berkaitan dengan kebutuhan pengguna. Hasil jamu
yang relevan ditampilkan pada bagian rekomendasi berdasarkan
data pada knowledge base."
""".strip()

    return prompt


# ============================================================
# FALLBACK ANSWER
# ============================================================

def build_fallback_answer(
    query,
    bahan,
    khasiat,
    results
):
    """
    Membuat jawaban fallback berdasarkan hasil retrieval.

    Fallback ini digunakan apabila Gemini:
    - menghasilkan jawaban kosong
    - menghasilkan jawaban terlalu pendek
    - menghasilkan jawaban yang terpotong
    - gagal menghasilkan jawaban
    """

    if not results:

        return (
            "Berdasarkan informasi pada knowledge base, "
            "sistem belum menemukan data jamu yang dapat "
            "digunakan untuk menjawab pertanyaan tersebut."
        )

    # --------------------------------------------------------
    # BAHAN + KHASIAT
    # --------------------------------------------------------

    if bahan and khasiat:

        bahan_text = ", ".join(
            bahan
        )

        khasiat_text = ", ".join(
            khasiat
        )

        return (
            "Berdasarkan informasi pada knowledge base, "
            f"terdapat data jamu yang berkaitan dengan "
            f"bahan {bahan_text} dan khasiat {khasiat_text}. "
            "Hasil jamu yang relevan ditampilkan pada bagian "
            "rekomendasi berdasarkan data yang tersedia "
            "pada knowledge base."
        )


    # --------------------------------------------------------
    # HANYA BAHAN
    # --------------------------------------------------------

    if bahan:

        bahan_text = ", ".join(
            bahan
        )

        return (
            "Berdasarkan informasi pada knowledge base, "
            f"terdapat data jamu yang mengandung bahan "
            f"{bahan_text}. Hasil jamu yang relevan "
            "ditampilkan pada bagian rekomendasi "
            "berdasarkan data yang tersedia."
        )


    # --------------------------------------------------------
    # HANYA KHASIAT
    # --------------------------------------------------------

    if khasiat:

        khasiat_text = ", ".join(
            khasiat
        )

        return (
            "Berdasarkan informasi pada knowledge base, "
            f"terdapat data jamu yang berkaitan dengan "
            f"khasiat {khasiat_text}. Hasil jamu yang "
            "relevan ditampilkan pada bagian rekomendasi "
            "berdasarkan data yang tersedia."
        )


    # --------------------------------------------------------
    # TIDAK ADA ENTITY
    # --------------------------------------------------------

    return (
        "Berdasarkan hasil pencarian pada knowledge base, "
        "sistem menemukan beberapa data jamu yang dapat "
        "digunakan sebagai referensi untuk pertanyaan "
        "pengguna. Hasil yang ditemukan ditampilkan pada "
        "bagian rekomendasi."
    )


# ============================================================
# VALIDATE GENERATED ANSWER
# ============================================================

def is_answer_incomplete(answer):
    """
    Mendeteksi output Gemini yang jelas tidak lengkap.
    """

    if not answer:
        return True

    answer = answer.strip()

    # Terlalu pendek
    if len(answer) < 50:
        return True

    # Tidak berakhir dengan tanda baca
    if answer[-1] not in ".!?":
        return True

    # Beberapa tanda bahwa output masih berupa potongan
    incomplete_endings = [
        "yang",
        "dan",
        "atau",
        "untuk",
        "dengan",
        "terdapat",
        "adalah",
        "berdasarkan",
        "yaitu",
        "serta",
        "dari"
    ]

    last_word = (
        answer
        .lower()
        .rstrip(".!?")
        .split()
    )

    if last_word:

        if last_word[-1] in incomplete_endings:

            return True

    return False


# ============================================================
# GEMINI REQUEST
# ============================================================

def generate_gemini(
    prompt,
    max_retries=2
):
    """
    Memanggil Gemini REST API.
    """

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],

        "generationConfig": {
            "maxOutputTokens": 2048
        }
    }


    for attempt in range(
        max_retries
    ):

        try:

            response = requests.post(
                GEMINI_URL,
                headers=headers,
                json=payload,
                timeout=(5, 25)
            )


            # =================================================
            # SUCCESS
            # =================================================

            if response.status_code == 200:

                data = response.json()

                candidates = data.get(
                    "candidates",
                    []
                )

                if not candidates:

                    return {
                        "status": "ERROR",
                        "answer": "",
                        "finish_reason": None,
                        "raw_response": data
                    }


                candidate = candidates[0]

                content = candidate.get(
                    "content",
                    {}
                )

                parts = content.get(
                    "parts",
                    []
                )

                text_parts = [
                    part.get("text", "")
                    for part in parts
                    if part.get("text")
                ]

                answer = "\n".join(
                    text_parts
                ).strip()


                finish_reason = candidate.get(
                    "finishReason"
                )
                print("[GEMINI] finishReason:", finish_reason)
                print("[GEMINI] Panjang jawaban:", len(answer))
                print("[GEMINI] Jawaban:", repr(answer[:500]))


                print(
                    f"[GEMINI] finishReason: "
                    f"{finish_reason}"
                )


                return {
                    "status": "OK",
                    "answer": answer,
                    "finish_reason": finish_reason,
                    "raw_response": data
                }


            # =================================================
            # QUOTA
            # =================================================

            if response.status_code == 429:

                print(
                    "[GEMINI] HTTP 429 - quota"
                )

                return {
                    "status": "QUOTA",
                    "answer": "",
                    "finish_reason": None,
                    "raw_response": response.text
                }


            # =================================================
            # TEMPORARY ERROR
            # =================================================

            if response.status_code in {
                500,
                502,
                503,
                504
            }:

                if attempt < max_retries - 1:

                    wait_time = (
                        2 ** attempt
                    )

                    print(
                        f"[GEMINI] HTTP "
                        f"{response.status_code}. "
                        f"Retry dalam "
                        f"{wait_time} detik..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue


            # =================================================
            # OTHER ERROR
            # =================================================

            print(
                f"[GEMINI] HTTP "
                f"{response.status_code}"
            )

            return {
                "status": "ERROR",
                "answer": "",
                "finish_reason": None,
                "raw_response": response.text
            }


        except requests.RequestException as e:

            print(
                f"[GEMINI] Request error: {e}"
            )

            if attempt < max_retries - 1:

                wait_time = (
                    2 ** attempt
                )

                print(
                    f"Retry dalam "
                    f"{wait_time} detik..."
                )

                time.sleep(
                    wait_time
                )

                continue


            return {
                "status": "ERROR",
                "answer": "",
                "finish_reason": None,
                "raw_response": str(e)
            }


    return {
        "status": "ERROR",
        "answer": "",
        "finish_reason": None,
        "raw_response": None
    }


# ============================================================
# RAG PIPELINE
# ============================================================

def generate_rag(query):
    """
    Pipeline:

    Query
      ↓
    Retrieval
      ↓
    Context
      ↓
    Gemini
      ↓
    Validation
      ↓
    Answer
    """

    # ========================================================
    # RETRIEVAL
    # ========================================================

    retrieval_result = retrieve(
        query
    )

    results = retrieval_result[
        "results"
    ]

    bahan = retrieval_result[
        "bahan"
    ]

    khasiat = retrieval_result[
        "khasiat"
    ]


    # ========================================================
    # NO RETRIEVAL
    # ========================================================

    if not results:

        return {
            "query": query,
            "bahan": bahan,
            "khasiat": khasiat,
            "results": [],
            "answer": build_fallback_answer(
                query=query,
                bahan=bahan,
                khasiat=khasiat,
                results=[]
            ),
            "status": "NO_RETRIEVAL"
        }


    # ========================================================
    # BUILD PROMPT
    # ========================================================

    prompt = build_prompt(
        query=query,
        bahan=bahan,
        khasiat=khasiat,
        results=results
    )


    # ========================================================
    # GEMINI
    # ========================================================

    generation = generate_gemini(
        prompt
    )

    generated_answer = generation.get(
        "answer",
        ""
    )

    gemini_status = generation.get(
        "status",
        "ERROR"
    )


    # ========================================================
    # VALIDATE GEMINI ANSWER
    # ========================================================

    if (
        gemini_status == "OK"
        and not is_answer_incomplete(
            generated_answer
        )
    ):

        final_answer = generated_answer

        final_status = "OK"


    else:

        print(
            "[RAG] Output Gemini tidak digunakan."
        )

        print(
            "[RAG] Menggunakan fallback answer."
        )

        final_answer = build_fallback_answer(
            query=query,
            bahan=bahan,
            khasiat=khasiat,
            results=results
        )

        final_status = (
            "OK_FALLBACK"
        )


    # ========================================================
    # RETURN
    # ========================================================

    return {
        "query": query,
        "bahan": bahan,
        "khasiat": khasiat,
        "results": results,
        "answer": final_answer,
        "status": final_status,
        "raw_response": generation.get(
            "raw_response"
        )
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    test_query = (
        "jamu apa yang mengandung jahe "
        "untuk menambah nafsu makan"
    )


    print("=" * 80)
    print("TEST RAG GENERATION")
    print("=" * 80)


    print("\nQuery:")
    print(test_query)


    result = generate_rag(
        test_query
    )


    print("\nBAHAN:")
    print(
        result["bahan"]
    )


    print("\nKHASIAT:")
    print(
        result["khasiat"]
    )


    print("\nRETRIEVED IDS:")

    print([
        item["id_jamu"]
        for item in result["results"]
    ])


    print("\nSTATUS:")

    print(
        result["status"]
    )


    print("\n" + "-" * 80)
    print("GENERATED ANSWER")
    print("-" * 80)


    print(
        result["answer"]
    )