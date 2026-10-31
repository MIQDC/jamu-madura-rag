// ============================================================
// ELEMENTS
// ============================================================

const queryForm = document.getElementById("queryForm");
const queryInput = document.getElementById("queryInput");

const askButton = document.getElementById("askButton");
const buttonText = document.getElementById("buttonText");

const charCounter = document.getElementById("charCounter");

const loading = document.getElementById("loading");

const errorBox = document.getElementById("errorBox");
const errorMessage = document.getElementById("errorMessage");

const resultSection = document.getElementById("resultSection");

const bahanContainer =
    document.getElementById("bahanContainer");

const khasiatContainer =
    document.getElementById("khasiatContainer");

const answerContent =
    document.getElementById("answerContent");

const recommendationsContainer =
    document.getElementById("recommendationsContainer");


// ============================================================
// CHARACTER COUNTER
// ============================================================

queryInput.addEventListener("input", () => {

    const length = queryInput.value.length;

    charCounter.textContent =
        `${length} / 500`;

});


// ============================================================
// SHOW / HIDE
// ============================================================

function showLoading() {

    loading.classList.remove("hidden");

    errorBox.classList.add("hidden");

    resultSection.classList.add("hidden");

    askButton.disabled = true;

    buttonText.textContent =
        "Memproses...";

}


function hideLoading() {

    loading.classList.add("hidden");

    askButton.disabled = false;

    buttonText.textContent =
        "Tanya Sekarang";

}


function showError(message) {

    errorMessage.textContent =
        message;

    errorBox.classList.remove("hidden");

    resultSection.classList.add("hidden");

}


function hideError() {

    errorBox.classList.add("hidden");

}


// ============================================================
// ESCAPE HTML
// Mencegah data response dimasukkan sebagai HTML mentah.
// ============================================================

function escapeHtml(value) {

    if (value === null ||
        value === undefined) {

        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// RENDER ENTITY
// ============================================================

function renderEntities(
    container,
    entities
) {

    container.innerHTML = "";

    if (
        !entities ||
        entities.length === 0
    ) {

        container.textContent =
            "Tidak terdeteksi";

        return;
    }


    entities.forEach(entity => {

        const tag =
            document.createElement("span");

        tag.className =
            "entity-tag";

        tag.textContent =
            entity;

        container.appendChild(tag);

    });

}


// ============================================================
// RENDER ANSWER
// ============================================================

// function renderAnswer(answer) {

//     if (!answer) {

//         answerContent.textContent =
//             "Jawaban tidak tersedia.";

//         return;
//     }


//     answerContent.textContent =
//         answer;

// }

// ============================================================
// FORMAT ANSWER
// ============================================================

function formatAnswer(text) {

    if (!text) {
        return "";
    }

    // Escape HTML terlebih dahulu
    let safeText = escapeHtml(text);

    // Hapus horizontal rule Markdown
    safeText = safeText.replace(
        /^---$/gm,
        ""
    );

    // Heading ### / ## / #
    safeText = safeText.replace(
        /^###\s+(.+)$/gm,
        '<h4 class="answer-heading">$1</h4>'
    );

    safeText = safeText.replace(
        /^##\s+(.+)$/gm,
        '<h4 class="answer-heading">$1</h4>'
    );

    safeText = safeText.replace(
        /^#\s+(.+)$/gm,
        '<h4 class="answer-heading">$1</h4>'
    );

    // Bold **text**
    safeText = safeText.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Bullet dengan -
    safeText = safeText.replace(
        /^-\s+(.+)$/gm,
        '<div class="answer-bullet">$1</div>'
    );

    // Bullet dengan *
    safeText = safeText.replace(
        /^\*\s+(.+)$/gm,
        '<div class="answer-bullet">$1</div>'
    );

    // Nomor 1. 2. 3.
    safeText = safeText.replace(
        /^(\d+)\.\s+(.+)$/gm,
        '<div class="answer-number"><span>$1.</span> $2</div>'
    );

    // Baris kosong
    safeText = safeText.replace(
        /\n{2,}/g,
        "<div class=\"answer-space\"></div>"
    );

    // Satu baris baru
    safeText = safeText.replace(
        /\n/g,
        "<br>"
    );

    return safeText;
}


// ============================================================
// RENDER ANSWER
// ============================================================

function renderAnswer(answer) {

    if (!answer) {

        answerContent.innerHTML =
            "<p>Jawaban tidak tersedia.</p>";

        return;
    }

    answerContent.innerHTML =
        formatAnswer(answer);
}

// ============================================================
// RENDER RECOMMENDATIONS
// ============================================================

// function renderRecommendations(
//     recommendations
// ) {

//     recommendationsContainer.innerHTML = "";


//     if (
//         !recommendations ||
//         recommendations.length === 0
//     ) {

//         recommendationsContainer.innerHTML = `
//             <div class="recommendation-card">
//                 <h4>
//                     Tidak ada rekomendasi
//                 </h4>

//                 <p class="recommendation-id">
//                     Sistem tidak menemukan dokumen
//                     yang sesuai.
//                 </p>
//             </div>
//         `;

//         return;
//     }


//     recommendations.forEach(item => {

//         const card =
//             document.createElement("article");

//         card.className =
//             "recommendation-card";


//         card.innerHTML = `

//             <div class="recommendation-rank">
//                 ${escapeHtml(item.rank)}
//             </div>

//             <h4>
//                 ${escapeHtml(item.nama_jamu)}
//             </h4>

//             <div class="recommendation-id">
//                 ID Jamu: ${escapeHtml(item.id_jamu)}
//             </div>

//             <div class="recommendation-info">

//                 <div class="info-item">

//                     <strong>
//                         Kandungan
//                     </strong>

//                     <span>
//                         ${escapeHtml(item.kandungan)}
//                     </span>

//                 </div>


//                 <div class="info-item">

//                     <strong>
//                         Khasiat
//                     </strong>

//                     <span>
//                         ${escapeHtml(item.khasiat)}
//                     </span>

//                 </div>


//                 <div class="info-item">

//                     <strong>
//                         Aturan Minum
//                     </strong>

//                     <span>
//                         ${escapeHtml(item.aturan_minum)}
//                     </span>

//                 </div>


//                 <div class="info-item">

//                     <strong>
//                         Efek Samping
//                     </strong>

//                     <span>
//                         ${escapeHtml(item.efek_samping)}
//                     </span>

//                 </div>


//                 <div class="info-item">

//                     <strong>
//                         Produsen
//                     </strong>

//                     <span>
//                         ${escapeHtml(item.produsen)}
//                     </span>

//                 </div>


//                 <div class="info-item">

//                     <strong>
//                         Kabupaten
//                     </strong>

//                     <span>
//                         ${escapeHtml(item.kabupaten)}
//                     </span>

//                 </div>

//             </div>
//         `;


//         recommendationsContainer.appendChild(
//             card
//         );

//     });

// }

// ============================================================
// RENDER RECOMMENDATIONS
// ============================================================

function renderRecommendations(
    recommendations
) {

    recommendationsContainer.innerHTML = "";


    if (
        !recommendations ||
        recommendations.length === 0
    ) {

        recommendationsContainer.innerHTML = `
            <div class="recommendation-card">
                <h4>
                    Tidak ada rekomendasi
                </h4>

                <p class="recommendation-id">
                    Sistem tidak menemukan dokumen
                    yang sesuai.
                </p>
            </div>
        `;

        return;
    }


    recommendations.forEach(item => {

        const card =
            document.createElement("article");

        card.className =
            "recommendation-card";


        // ----------------------------------------------------
        // FORMAT SCORE
        // ----------------------------------------------------

        const similarity =
            Number(
                item.semantic_similarity
            );

        const entityRatio =
            Number(
                item.entity_ratio
            );


        const similarityText =
            Number.isFinite(similarity)
                ? similarity.toFixed(4)
                : "-";


        const entityMatchText =
            `${item.matched_entity ?? 0}/` +
            `${item.total_entity ?? 0}`;


        const entityPercent =
            Number.isFinite(entityRatio)
                ? `${(entityRatio * 100).toFixed(0)}%`
                : "0%";


        // ----------------------------------------------------
        // CARD
        // ----------------------------------------------------

        card.innerHTML = `

            <div class="recommendation-top">

                <div class="recommendation-rank">
                    ${escapeHtml(item.rank)}
                </div>

                <div class="recommendation-score">

                    <span class="score-label">
                        Similarity
                    </span>

                    <strong>
                        ${escapeHtml(similarityText)}
                    </strong>

                </div>

            </div>


            <h4>
                ${escapeHtml(item.nama_jamu)}
            </h4>


            <div class="recommendation-id">
                ID Jamu: ${escapeHtml(item.id_jamu)}
            </div>


            <div class="entity-match">

                <span>
                    Entity Match
                </span>

                <strong>
                    ${escapeHtml(entityMatchText)}
                </strong>

                <span>
                    (${escapeHtml(entityPercent)})
                </span>

            </div>


            <div class="recommendation-info">

                <div class="info-item">

                    <strong>
                        Kandungan
                    </strong>

                    <span>
                        ${escapeHtml(item.kandungan)}
                    </span>

                </div>


                <div class="info-item">

                    <strong>
                        Khasiat
                    </strong>

                    <span>
                        ${escapeHtml(item.khasiat)}
                    </span>

                </div>


                <div class="info-item">

                    <strong>
                        Aturan Minum
                    </strong>

                    <span>
                        ${escapeHtml(item.aturan_minum)}
                    </span>

                </div>


                <div class="info-item">

                    <strong>
                        Efek Samping
                    </strong>

                    <span>
                        ${escapeHtml(item.efek_samping)}
                    </span>

                </div>


                <div class="info-item">

                    <strong>
                        Produsen
                    </strong>

                    <span>
                        ${escapeHtml(item.produsen)}
                    </span>

                </div>


                <div class="info-item">

                    <strong>
                        Kabupaten
                    </strong>

                    <span>
                        ${escapeHtml(item.kabupaten)}
                    </span>

                </div>

            </div>
        `;


        recommendationsContainer.appendChild(
            card
        );

    });

}

// ============================================================
// RENDER RESULT
// ============================================================

function renderResult(data) {

    renderEntities(
        bahanContainer,
        data.entities?.bahan || []
    );


    renderEntities(
        khasiatContainer,
        data.entities?.khasiat || []
    );


    renderAnswer(
        data.answer || ""
    );


    renderRecommendations(
        data.recommendations || []
    );


    resultSection.classList.remove(
        "hidden"
    );


    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// ============================================================
// SUBMIT FORM
// ============================================================

queryForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        hideError();


        const query =
            queryInput.value.trim();


        // ----------------------------------------------------
        // VALIDATION
        // ----------------------------------------------------

        if (!query) {

            showError(
                "Pertanyaan tidak boleh kosong."
            );

            queryInput.focus();

            return;
        }


        if (query.length > 500) {

            showError(
                "Pertanyaan maksimal 500 karakter."
            );

            return;
        }


        // ----------------------------------------------------
        // START LOADING
        // ----------------------------------------------------

        showLoading();


        try {

            // ------------------------------------------------
            // REQUEST KE FLASK
            // ------------------------------------------------

            const response =
                await fetch(
                    "/api/ask",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            query: query
                        })
                    }
                );


            // ------------------------------------------------
            // PARSE RESPONSE
            // ------------------------------------------------

            const data =
                await response.json();


            // ------------------------------------------------
            // HTTP ERROR
            // ------------------------------------------------

            if (!response.ok) {

                throw new Error(
                    data.message ||
                    "Terjadi kesalahan pada server."
                );

            }


            // ------------------------------------------------
            // APPLICATION ERROR
            // ------------------------------------------------

            if (
                data.status === "ERROR"
            ) {

                throw new Error(
                    data.message ||
                    "Terjadi kesalahan saat memproses query."
                );

            }


            // ------------------------------------------------
            // RENDER
            // ------------------------------------------------

            renderResult(data);


        }
        catch (error) {

            console.error(
                "API ERROR:",
                error
            );

            showError(
                error.message ||
                "Tidak dapat memproses pertanyaan."
            );

        }
        finally {

            hideLoading();

        }

    }
);