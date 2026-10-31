from flask import Flask, render_template, request, jsonify

from rag.generation import generate_rag
from rag.retrieval import retrieve


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# API RETRIEVE
# RETRIEVAL ONLY
# ============================================================

@app.route("/api/retrieve", methods=["POST"])
def api_retrieve():

    try:

        # ----------------------------------------------------
        # Ambil JSON
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status": "ERROR",
                "message": "Request JSON tidak ditemukan."
            }), 400


        # ----------------------------------------------------
        # Ambil query
        # ----------------------------------------------------

        query = str(
            data.get("query", "")
        ).strip()


        # ----------------------------------------------------
        # Validasi query
        # ----------------------------------------------------

        if not query:

            return jsonify({
                "status": "ERROR",
                "message": "Query tidak boleh kosong."
            }), 400


        # ----------------------------------------------------
        # Batasi panjang query
        # ----------------------------------------------------

        if len(query) > 500:

            return jsonify({
                "status": "ERROR",
                "message": (
                    "Query terlalu panjang. "
                    "Maksimal 500 karakter."
                )
            }), 400


        # ----------------------------------------------------
        # Jalankan retrieval
        # ----------------------------------------------------

        result = retrieve(
            query
        )


        # ----------------------------------------------------
        # Format hasil retrieval
        # ----------------------------------------------------

        recommendations = []

        for item in result.get(
            "results",
            []
        ):

            recommendations.append({

                "rank": item.get(
                    "rank"
                ),

                "id_jamu": item.get(
                    "id_jamu"
                ),

                "nama_jamu": item.get(
                    "nama_jamu"
                ),

                "kandungan": item.get(
                    "kandungan"
                ),

                "khasiat": item.get(
                    "khasiat"
                ),

                "aturan_minum": item.get(
                    "aturan_minum"
                ),

                "efek_samping": item.get(
                    "efek_samping"
                ),

                "jenis": item.get(
                    "jenis"
                ),

                "produsen": item.get(
                    "produsen"
                ),

                "kategori": item.get(
                    "kategori"
                ),

                "lokasi_pemasaran": item.get(
                    "lokasi_pemasaran"
                ),

                "lokasi_produksi": item.get(
                    "lokasi_produksi"
                ),

                "kabupaten": item.get(
                    "kabupaten"
                ),

                "perizinan": item.get(
                    "perizinan"
                ),

                "semantic_similarity": item.get(
                    "semantic_similarity"
                ),

                "matched_entity": item.get(
                    "matched_entity"
                ),

                "total_entity": item.get(
                    "total_entity"
                ),

                "entity_ratio": item.get(
                    "entity_ratio"
                )
            })


        # ----------------------------------------------------
        # Return response
        # ----------------------------------------------------

        return jsonify({

            "status": "OK",

            "query": query,

            "entities": {

                "bahan": result.get(
                    "bahan",
                    []
                ),

                "khasiat": result.get(
                    "khasiat",
                    []
                )
            },

            "recommendations": recommendations
        })


    except Exception as e:

        print(
            f"[ERROR] /api/retrieve: {e}"
        )

        return jsonify({

            "status": "ERROR",

            "message": (
                "Terjadi kesalahan pada "
                "retrieval server."
            ),

            "detail": str(e)
        }), 500


# ============================================================
# API ASK
# ============================================================

@app.route("/api/ask", methods=["POST"])
def ask():

    try:

        # ----------------------------------------------------
        # Ambil JSON
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status": "ERROR",
                "message": "Request JSON tidak ditemukan."
            }), 400


        # ----------------------------------------------------
        # Ambil query
        # ----------------------------------------------------

        query = str(
            data.get("query", "")
        ).strip()


        # ----------------------------------------------------
        # Validasi query
        # ----------------------------------------------------

        if not query:

            return jsonify({
                "status": "ERROR",
                "message": "Pertanyaan tidak boleh kosong."
            }), 400


        # ----------------------------------------------------
        # Batasi panjang query
        # ----------------------------------------------------

        if len(query) > 500:

            return jsonify({
                "status": "ERROR",
                "message": (
                    "Pertanyaan terlalu panjang. "
                    "Maksimal 500 karakter."
                )
            }), 400


        # ----------------------------------------------------
        # Jalankan pipeline RAG
        # ----------------------------------------------------

        result = generate_rag(
            query
        )


        # ----------------------------------------------------
        # Format hasil retrieval
        # ----------------------------------------------------

        recommendations = []

        for item in result.get(
            "results",
            []
        ):

            recommendations.append({

                "rank": item.get(
                    "rank"
                ),

                "id_jamu": item.get(
                    "id_jamu"
                ),

                "nama_jamu": item.get(
                    "nama_jamu"
                ),

                "kandungan": item.get(
                    "kandungan"
                ),

                "khasiat": item.get(
                    "khasiat"
                ),

                "aturan_minum": item.get(
                    "aturan_minum"
                ),

                "efek_samping": item.get(
                    "efek_samping"
                ),

                "jenis": item.get(
                    "jenis"
                ),

                "produsen": item.get(
                    "produsen"
                ),

                "kategori": item.get(
                    "kategori"
                ),

                "lokasi_pemasaran": item.get(
                    "lokasi_pemasaran"
                ),

                "lokasi_produksi": item.get(
                    "lokasi_produksi"
                ),

                "kabupaten": item.get(
                    "kabupaten"
                ),

                "perizinan": item.get(
                    "perizinan"
                ),

                "semantic_similarity": item.get(
                    "semantic_similarity"
                ),

                "matched_entity": item.get(
                    "matched_entity"
                ),

                "total_entity": item.get(
                    "total_entity"
                ),

                "entity_ratio": item.get(
                    "entity_ratio"
                )
            })


        # ----------------------------------------------------
        # Return response
        # ----------------------------------------------------

        return jsonify({

            "status": result.get(
                "status",
                "UNKNOWN"
            ),

            "query": result.get(
                "query",
                query
            ),

            "entities": {

                "bahan": result.get(
                    "bahan",
                    []
                ),

                "khasiat": result.get(
                    "khasiat",
                    []
                )
            },

            "answer": result.get(
                "answer",
                ""
            ),

            "recommendations": recommendations
        })


    except Exception as e:

        print(
            f"[ERROR] /api/ask: {e}"
        )

        return jsonify({

            "status": "ERROR",

            "message": (
                "Terjadi kesalahan pada "
                "server."
            ),

            "detail": str(e)
        }), 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SISTEM TANYA JAWAB DAN REKOMENDASI JAMU MADURA")
    print("=" * 70)
    print("Server berjalan di:")
    print("http://127.0.0.1:5000")
    print("=" * 70)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )