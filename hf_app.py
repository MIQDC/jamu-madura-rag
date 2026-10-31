import gradio as gr
from rag.generation import generate_rag


def ask_jamu(query):
    query = (query or "").strip()

    if not query:
        return "Silakan masukkan pertanyaan.", {}, []

    if len(query) > 500:
        return "Pertanyaan maksimal 500 karakter.", {}, []

    try:
        result = generate_rag(query)

        entities = {
            "Bahan": result.get("bahan", []),
            "Khasiat": result.get("khasiat", []),
            "Status": result.get("status", "UNKNOWN")
        }

        recommendations = []

        for item in result.get("results", []):
            recommendations.append({
                "Peringkat": item.get("rank"),
                "ID Jamu": item.get("id_jamu"),
                "Nama Jamu": item.get("nama_jamu"),
                "Kandungan": item.get("kandungan"),
                "Khasiat": item.get("khasiat"),
                "Aturan Minum": item.get("aturan_minum"),
                "Efek Samping": item.get("efek_samping"),
                "Jenis": item.get("jenis"),
                "Produsen": item.get("produsen"),
                "Kategori": item.get("kategori"),
                "Lokasi Pemasaran": item.get("lokasi_pemasaran"),
                "Lokasi Produksi": item.get("lokasi_produksi"),
                "Kabupaten": item.get("kabupaten"),
                "Perizinan": item.get("perizinan"),
                "Semantic Similarity": item.get("semantic_similarity"),
                "Matched Entity": item.get("matched_entity"),
                "Total Entity": item.get("total_entity"),
                "Entity Ratio": item.get("entity_ratio")
            })

        answer = result.get("answer", "Jawaban tidak tersedia.")

        return answer, entities, recommendations

    except Exception as e:
        print(f"[GRADIO ERROR] {e}")
        return (
            "Terjadi kesalahan saat memproses pertanyaan. Silakan coba kembali.",
            {"Status": "ERROR", "Detail": str(e)},
            []
        )


with gr.Blocks(title="Sistem Tanya Jawab Jamu Madura") as demo:

    gr.Markdown(
        """
        # Sistem Tanya Jawab dan Rekomendasi Jamu Tradisional Madura

        Sistem berbasis Retrieval-Augmented Generation (RAG)
        menggunakan Word2Vec, Bi-LSTM, FAISS, dan Gemini.
        """
    )

    query = gr.Textbox(
        label="Pertanyaan",
        placeholder="Contoh: Jamu apa yang mengandung jahe untuk menambah nafsu makan?",
        lines=2,
        max_lines=4
    )

    submit = gr.Button("Cari dan Tanyakan", variant="primary")

    gr.Markdown("## Jawaban")
    answer = gr.Markdown()

    gr.Markdown("## Informasi Entitas")
    entities = gr.JSON(label="Bahan, Khasiat, dan Status")

    gr.Markdown("## Rekomendasi Jamu")
    recommendations = gr.JSON(label="Hasil Retrieval")

    submit.click(
        fn=ask_jamu,
        inputs=query,
        outputs=[answer, entities, recommendations]
    )

    query.submit(
        fn=ask_jamu,
        inputs=query,
        outputs=[answer, entities, recommendations]
    )

    gr.Examples(
        examples=[
            ["Jamu apa yang mengandung jahe untuk menambah nafsu makan?"],
            ["Jamu apa yang berkhasiat untuk melancarkan ASI?"],
            ["Apa saja kandungan jamu untuk menjaga kesehatan tubuh?"]
        ],
        inputs=query
    )


if __name__ == "__main__":
    demo.queue().launch()
