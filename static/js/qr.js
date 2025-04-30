// Función para generar código QR
function generateQR(data) {
    return new QRCode(document.createElement("div"), {
        text: data,
        width: 128,
        height: 128,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H
    });
}

// Función para mostrar QR en modal
function showQRModal(studentId, studentName) {
    const modalHtml = `
        <div class="modal fade" id="qrModal-${studentId}" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Código QR de ${studentName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center">
                        <div id="qrcode-${studentId}" class="d-inline-block p-3 bg-white rounded"></div>
                        <p class="mt-3">ID: ${studentId}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="downloadQR(${studentId})">
                            <i class="fas fa-download me-2"></i>Descargar QR
                        </button>
                    </div>
                </div>
            </div>
        </div>`;

    // Agregar modal al body si no existe
    if (!document.getElementById(`qrModal-${studentId}`)) {
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Generar QR
    const qrContainer = document.getElementById(`qrcode-${studentId}`);
    qrContainer.innerHTML = '';
    const qr = generateQR(`STUDENT:${studentId}`);
    qrContainer.appendChild(qr._el);

    // Mostrar modal
    new bootstrap.Modal(document.getElementById(`qrModal-${studentId}`)).show();
}

// Función para descargar QR
function downloadQR(studentId) {
    const qrImage = document.querySelector(`#qrcode-${studentId} img`);
    const link = document.createElement('a');
    link.download = `qr-estudiante-${studentId}.png`;
    link.href = qrImage.src;
    link.click();
} 