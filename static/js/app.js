document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileChosen = document.getElementById('file-chosen');
    const fileList = document.getElementById('file-list');
    const mergeBtn = document.getElementById('merge-btn');
    const statusMessage = document.getElementById('status-message');
    const filenameInput = document.getElementById('filename-input');

    let selectedFiles = [];

    fileInput.addEventListener('change', (event) => {
        selectedFiles = Array.from(event.target.files);
        updateFileList();
    });

    function updateFileList() {
        fileList.innerHTML = '';
        fileChosen.textContent = `${selectedFiles.length} file(s) selected`;

        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.classList.add('file-item');
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <button onclick="removeFile(${index})">✖</button>
            `;
            fileList.appendChild(fileItem);
        });

        mergeBtn.disabled = selectedFiles.length === 0;
    }

    window.removeFile = (index) => {
        selectedFiles.splice(index, 1);
        fileInput.files = new DataTransfer().files;
        updateFileList();
    };

    mergeBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files', file));

        // Add custom filename to form data
        const customFilename = filenameInput.value.trim() || 'merged';
        formData.append('filename', customFilename);

        statusMessage.textContent = 'Merging PDFs...';
        statusMessage.className = 'status-message';

        try {
            const response = await fetch('/merge', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Use the custom filename for download
                a.download = customFilename.endsWith('.pdf') ? customFilename : `${customFilename}.pdf`;
                
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();

                statusMessage.textContent = 'PDFs merged successfully!';
                statusMessage.classList.add('success');
            } else {
                const errorText = await response.text();
                throw new Error(errorText);
            }
        } catch (error) {
            console.error('Error:', error);
            statusMessage.textContent = `Error: ${error.message}`;
            statusMessage.classList.add('error');
        }
    });
});