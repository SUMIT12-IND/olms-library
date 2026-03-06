// ── QR Code Scanner ─────────────────────────────
let videoStream = null;
let scanning = false;

function startScanner() {
    const video = document.getElementById('scannerVideo');
    const startBtn = document.getElementById('startScanBtn');
    const stopBtn = document.getElementById('stopScanBtn');

    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(function (stream) {
            videoStream = stream;
            video.srcObject = stream;
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            scanning = true;
            scanFrame();
        })
        .catch(function (err) {
            alert('Camera access denied. Please allow camera permissions.');
            console.error(err);
        });
}

function stopScanner() {
    scanning = false;
    if (videoStream) {
        videoStream.getTracks().forEach(t => t.stop());
        videoStream = null;
    }
    document.getElementById('startScanBtn').style.display = 'inline-block';
    document.getElementById('stopScanBtn').style.display = 'none';
}

function scanFrame() {
    if (!scanning) return;

    const video = document.getElementById('scannerVideo');
    const canvas = document.getElementById('scannerCanvas');
    const ctx = canvas.getContext('2d');

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Try to detect QR using a simple approach
        // For production, use a library like jsQR
        // Here we simulate with manual input fallback
    }

    requestAnimationFrame(scanFrame);
}

// Manual QR code input as fallback
function processQRManual() {
    const code = prompt('Enter QR code data (e.g., OLMS_BOOK_1):');
    if (!code) return;
    processQRCode(code);
}

function processQRCode(qrData) {
    fetch('/admin/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qr_data: qrData })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const result = document.getElementById('scanResult');
                document.getElementById('scannedTitle').textContent = data.book.title;
                document.getElementById('scannedAuthor').textContent = data.book.author;
                document.getElementById('scannedIsbn').textContent = data.book.isbn;
                document.getElementById('scannedAvailable').textContent = data.book.available;
                result.style.display = 'block';
                result.dataset.bookId = data.book.id;
            } else {
                alert(data.message);
            }
        });
}

function issueViaQR() {
    const bookId = document.getElementById('scanResult').dataset.bookId;
    const userId = document.getElementById('scanUserId').value;
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }

    fetch('/admin/api/scan/issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: bookId, user_id: userId, action: 'issue' })
    })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            if (data.success) {
                document.getElementById('scanResult').style.display = 'none';
            }
        });
}
