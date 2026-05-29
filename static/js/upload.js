/**
 * File Upload & Image Preview Logic
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. ID Card Upload Logic (Registration & Re-upload)
    const idFileInput = document.getElementById('file-upload');
    const idUploadArea = document.getElementById('id-upload-area');
    const idFileNameEl = document.getElementById('file-name');

    if (idFileInput && idUploadArea) {
        // Handle file change
        idFileInput.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                if (idFileNameEl) {
                    idFileNameEl.textContent = '✅ تم اختيار: ' + this.files[0].name;
                    idFileNameEl.classList.remove('hidden');
                }
                idUploadArea.classList.remove('border-gray-300');
                idUploadArea.classList.add('border-primary-400', 'bg-primary-50');
            } else {
                if (idFileNameEl) idFileNameEl.classList.add('hidden');
                idUploadArea.classList.add('border-gray-300');
                idUploadArea.classList.remove('border-primary-400', 'bg-primary-50');
            }
        });

        // Handle drag and drop for ID Card
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            idUploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            idUploadArea.addEventListener(eventName, () => {
                idUploadArea.classList.add('bg-primary-50', 'border-primary-400');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            idUploadArea.addEventListener(eventName, () => {
                idUploadArea.classList.remove('bg-primary-50', 'border-primary-400');
            }, false);
        });

        idUploadArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt.files && dt.files.length > 0) {
                idFileInput.files = dt.files;
                idFileInput.dispatchEvent(new Event('change'));
            }
        });
    }

    // 2. Listing Images Logic (Automatic Listener)
    const listingImagesInput = document.getElementById('listing-images');
    if (listingImagesInput) {
        listingImagesInput.addEventListener('change', function() {
            previewImages(this);
        });
    }
});

let selectedListingFiles = [];
let isProgrammaticChange = false;

/**
 * Preview multiple images before upload
 * Used in create/edit listing pages
 * @param {HTMLInputElement} input 
 */
function previewImages(input) {
    if (isProgrammaticChange) return;
    
    const preview = document.getElementById('image-preview');
    if (!preview) return;
    
    if (input.files && input.files.length > 0) {
        const inputFilesArray = Array.from(input.files);
        
        // Append only unique files (by name, size, lastModified)
        inputFilesArray.forEach(newFile => {
            const isDuplicate = selectedListingFiles.some(existingFile => 
                existingFile.name === newFile.name && 
                existingFile.size === newFile.size && 
                existingFile.lastModified === newFile.lastModified
            );
            if (!isDuplicate) {
                selectedListingFiles.push(newFile);
            }
        });
    }
    
    // ALWAYS synchronize input.files with selectedListingFiles list
    // This prevents browser file dialog cancellation from wiping out previously selected images
    isProgrammaticChange = true;
    const dt = new DataTransfer();
    selectedListingFiles.forEach(file => dt.items.add(file));
    input.files = dt.files;
    isProgrammaticChange = false;
    
    if (selectedListingFiles.length === 0) {
        preview.innerHTML = '';
        return;
    }
    
    renderListingPreviews(input, preview);
}

/**
 * Renders the HTML previews for selected files with delete options
 */
function renderListingPreviews(input, previewContainer) {
    previewContainer.innerHTML = '';
    
    selectedListingFiles.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const div = document.createElement('div');
            div.className = 'relative group aspect-square rounded-lg overflow-hidden border border-gray-200 shadow-sm bg-gray-50';
            div.innerHTML = `
                <img src="${e.target.result}" class="w-full h-full object-cover">
                <!-- Hover Overlay -->
                <div class="absolute inset-0 bg-black/25 opacity-0 group-hover:opacity-100 transition flex items-center justify-center pointer-events-none">
                    <i class="fa-solid fa-eye text-white text-sm"></i>
                </div>
                <!-- Delete Button -->
                <button type="button" class="absolute top-1.5 right-1.5 bg-red-500 hover:bg-red-600 text-white w-7 h-7 rounded-full shadow-md flex items-center justify-center transition opacity-90 hover:opacity-100 hover:scale-105 focus:outline-none" title="حذف الصورة">
                    <i class="fa-solid fa-trash-can text-[10px]"></i>
                </button>
            `;
            
            // Add click listener to the delete button
            const deleteBtn = div.querySelector('button');
            deleteBtn.addEventListener('click', function(event) {
                event.stopPropagation();
                removeListingImage(index, input, previewContainer);
            });
            
            previewContainer.appendChild(div);
        }
        reader.readAsDataURL(file);
    });
}

/**
 * Removes a specific image and updates the inputs filelist
 */
function removeListingImage(index, input, previewContainer) {
    selectedListingFiles.splice(index, 1);
    
    isProgrammaticChange = true;
    const dt = new DataTransfer();
    selectedListingFiles.forEach(file => dt.items.add(file));
    input.files = dt.files;
    isProgrammaticChange = false;
    
    renderListingPreviews(input, previewContainer);
}

/**
 * Validates file size before upload
 * @param {HTMLInputElement} input 
 * @param {number} maxSizeMB 
 */
function validateFileSize(input, maxSizeMB = 10) {
    if (input.files && input.files[0]) {
        const fileSize = input.files[0].size / 1024 / 1024;
        if (fileSize > maxSizeMB) {
            if (window.Swal) {
                Swal.fire({
                    icon: 'error',
                    title: 'خطأ في حجم الملف',
                    text: `حجم الملف كبير جداً. الحد الأقصى هو ${maxSizeMB} ميجابايت.`,
                    confirmButtonText: 'حسناً'
                });
            } else {
                alert(`حجم الملف كبير جداً. الحد الأقصى هو ${maxSizeMB} ميجابايت.`);
            }
            input.value = '';
            return false;
        }
    }
    return true;
}
