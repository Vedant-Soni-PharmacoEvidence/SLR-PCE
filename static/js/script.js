// landing.html


document.addEventListener('DOMContentLoaded', function () {
    // Get the "Upload Model" button
    var getstarted = document.getElementById('getstarted');

    // Add click event listener
    getstarted.addEventListener('click', function () {
        // Redirect to the "/upload" route
        // window.location.href = '/signin';
        window.location.href = '/model';
    });
});


// signin.html

function showLoader() {
    document.getElementById('loader').style.display = 'flex';
    setTimeout(function () {
        document.getElementById('loader').style.display = 'none';
    }, 3000); // Adjust the duration (in milliseconds) as needed
}

// home.html

document.addEventListener('DOMContentLoaded', function () {
    // Get the "Upload Model" button
    var continueto = document.getElementById('continueto');

    // Add click event listener
    continueto.addEventListener('click', function () {
        // Redirect to the "/upload" route
        window.location.href = '/model';
    });
});
//////////////////////////upload file button /////////////////////////////////
function uploadAndSelectModel() {
    var fileInput = document.getElementById('fileInput');
    
    if (fileInput.files.length === 0) {
        alert("Please select an Excel file.");
    } else {
        window.location.href = '/model';
    }
    
}


function handleDragOver(event) {
    event.preventDefault();
    const dropArea = document.getElementById('dropArea');
    dropArea.classList.add('drag-over');
  }
  
  function handleDrop(event) {
    event.preventDefault();
    const dropArea = document.getElementById('dropArea');
    dropArea.classList.remove('drag-over');
  
    const fileInput = document.getElementById('fileInput');
    fileInput.files = event.dataTransfer.files;
  
    handleFileSelection();
  }
  
  function handleFileSelection() {
    const fileInput = document.getElementById('fileInput');
    const dropArea = document.getElementById('dropArea');
    const fileNameDisplay = dropArea.querySelector('p');
  
    if (fileInput.files.length > 0) {
      const fileName = fileInput.files[0].name;
      fileNameDisplay.innerText = fileName;
    }
  }

// ////////////////////model.html handsontable/////////////////////////////////
document.addEventListener('DOMContentLoaded', function () {
    uploadFile();

    
});

document.addEventListener('DOMContentLoaded', function () {
    // Function to update model information when an AI model is selected
    function selectAI(model) {
        const selectedModel = document.querySelector(`.ai-button[data-id="${model}"]`);

        if (selectedModel) {
            document.getElementById('model-name-info').textContent = selectedModel.dataset.model;
            document.getElementById('developer-info').textContent = selectedModel.dataset.developer;
            document.getElementById('year-info').textContent = selectedModel.dataset.year;
            document.getElementById('accuracy-info').textContent = selectedModel.dataset.accuracy;

            document.getElementById('Analyse').disabled = false;
        } else {
            console.error(`Element with data-id="${model}" not found.`);
        }
    }

    // Function to send selected model information to the backend

    function analyseModel() {
        document.getElementById("loading").style.display = "block";
        const modelName = document.getElementById('model-name-info').textContent;
    
        // Replace spaces with underscores in the model name for the URL
        const modelNameForURL = modelName.replace(/[\s()]+/g, '_');
    
        
    
        // Send the selected model name to the appropriate backend route based on the model
        fetch(`/${modelNameForURL.toLowerCase()}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model: modelName }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById("loading").style.display = "none";
            alert('File has been successfully saved as GPT4_results.xlsx!');
            
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById("loading").style.display = "none";
            })
            
    }
    

    // Add event listeners to AI model buttons
    const aiButtons = document.querySelectorAll('.ai-button');
    aiButtons.forEach(button => {
        button.addEventListener('click', function () {
            const modelId = this.dataset.id;
            selectAI(modelId);
        });
    });

    // Add event listener to Analyse button
    document.getElementById('Analyse').addEventListener('click', analyseModel);
});



//////////////////////////////////////////////////////////////////////////////////////////

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (result.success) {
                // Show success message or perform any other action on success
                alert('File uploaded successfully!');
                console.log("file was saved and ready for analysis");

                
            } else {
                console.error('File upload failed');
            }
        } catch (error) {
            console.error('Error during file upload:', error);
        }
    }
}












document.addEventListener("DOMContentLoaded", async function () {
    try {
        const response = await fetch("/get_publication_types_chart");
        const data = await response.json();

        if (data.success) {
            // Display the HTML plot
            const plotContainer = document.getElementById("publicationTypesChartContainer");
            plotContainer.innerHTML = data.plot_data;
        } else {
            console.error("Error fetching publication types chart data:", data.error);
        }
    } catch (error) {
        console.error("Error processing publication types chart data:", error);
    }
});




