/**
 * FOS Upload Page Logic
 * Handles drag-drop file upload and processing
 */

let selectedFile = null;

/**
 * Initialize upload page
 */
function initUpload() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");

  // Drag and drop events
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  });

  // File input change
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  // Click to browse
  dropZone.addEventListener("click", (e) => {
    if (e.target.tagName !== "INPUT" && e.target.tagName !== "LABEL") {
      fileInput.click();
    }
  });
}

/**
 * Handle selected file
 */
function handleFile(file) {
  // Validate file type
  const validTypes = [".csv", ".xlsx", ".xls"];
  const extension = "." + file.name.split(".").pop().toLowerCase();

  if (!validTypes.includes(extension)) {
    showResult({
      success: false,
      message: "Invalid file type. Please upload CSV or Excel files.",
    });
    return;
  }

  selectedFile = file;

  // Show file info
  document.getElementById("file-name").textContent = file.name;
  document.getElementById("file-size").textContent = formatFileSize(file.size);
  document.getElementById("file-info").classList.remove("d-none");

  // Enable upload button
  document.getElementById("upload-btn").disabled = false;

  // Hide previous result
  document.getElementById("upload-result").classList.add("d-none");
}

/**
 * Clear selected file
 */
function clearFile() {
  selectedFile = null;
  document.getElementById("file-info").classList.add("d-none");
  document.getElementById("upload-btn").disabled = true;
  document.getElementById("file-input").value = "";
}

/**
 * Upload and process file
 */
async function uploadFile() {
  if (!selectedFile) return;

  const fileType = document.querySelector(
    'input[name="file_type"]:checked',
  ).value;

  // Show progress
  document.getElementById("upload-btn").disabled = true;
  document.getElementById("upload-progress").classList.remove("d-none");
  document.getElementById("upload-result").classList.add("d-none");

  try {
    // Create form data
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("file_type", fileType);

    // Upload
    const response = await fetch("/api/upload", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${api.getToken()}`,
      },
      body: formData,
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Upload failed");
    }

    showResult(result);
    addToRecentUploads(selectedFile.name, fileType, result.success);

    // Clear file on success
    if (result.success) {
      clearFile();
    }
  } catch (error) {
    showResult({
      success: false,
      message: error.message || "Upload failed",
    });
  } finally {
    document.getElementById("upload-progress").classList.add("d-none");
    document.getElementById("upload-btn").disabled = !selectedFile;
  }
}

/**
 * Show upload result
 */
function showResult(result) {
  const resultDiv = document.getElementById("upload-result");
  resultDiv.classList.remove("d-none");

  if (result.success) {
    resultDiv.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>
                <strong>Success!</strong> ${result.message}
                ${result.rows_processed ? `<br><small>${result.rows_processed} rows processed</small>` : ""}
                ${result.columns_found ? `<br><small class="text-muted">Columns: ${result.columns_found.slice(0, 5).join(", ")}${result.columns_found.length > 5 ? "..." : ""}</small>` : ""}
            </div>
        `;
  } else {
    resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>Error:</strong> ${result.message}
                ${result.columns_found ? `<br><small class="text-muted">Columns found: ${result.columns_found.join(", ")}</small>` : ""}
            </div>
        `;
  }
}

/**
 * Add to recent uploads list
 */
function addToRecentUploads(filename, fileType, success) {
  const list = document.getElementById("recent-uploads");
  const firstItem = list.querySelector("li");

  // Remove "no recent uploads" message if present
  if (firstItem && firstItem.textContent.includes("No recent")) {
    firstItem.remove();
  }

  // Add new item at top
  const icon = success
    ? "fa-check-circle text-success"
    : "fa-times-circle text-danger";
  const item = document.createElement("li");
  item.className =
    "list-group-item small d-flex justify-content-between align-items-center";
  item.innerHTML = `
        <span>
            <i class="fas ${icon} me-2"></i>
            ${filename}
        </span>
        <span class="badge bg-secondary">${fileType}</span>
    `;

  list.insertBefore(item, list.firstChild);

  // Keep only last 5
  while (list.children.length > 5) {
    list.removeChild(list.lastChild);
  }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}
