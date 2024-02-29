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

        // Capture the values of inclusionCriteria and exclusionCriteria
        var inclusionCriteria = document.getElementById("inclusionCriteriaInput").value;
        var exclusionCriteria = document.getElementById("exclusionCriteriaInput").value;

        // Log the values
        console.log('Inclusion Criteria:', inclusionCriteria);
        console.log('Exclusion Criteria:', exclusionCriteria);

        var criteria = {
            "inclusion_criteria": inclusionCriteria,
            "exclusion_criteria": exclusionCriteria
            // Add other data if needed
        };

        // Include both criteria and model in the body
        fetch(`/${modelNameForURL.toLowerCase()}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: modelName,
                criteria: criteria
            }),
        })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                document.getElementById("loading").style.display = "none";
                alert('File has been successfully saved as GPT4_results.xlsx!');
                window.location.href = "/dashboard"
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById("loading").style.display = "none";
            });
    }

    // Rest of your code...



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
function cleanDatabase() {
    fetch('/cleandb')
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            console.error('Error cleaning database:', error);
            alert('Error cleaning database. Please check the console for details.');
        });
}

// Function to fetch and update analysis info
function updateAnalysisInfo() {
    fetch('/analysis_info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('analyzedCount').innerText = data.analyzed_count;
            document.getElementById('remainingCount').innerText = data.remaining_count;
        })
        .catch(error => {
            console.error('Error fetching analysis info:', error);
        });
}

// Function to handle "Analyze Next Batch" button click
function secondpass() {
    // Add logic for analyzing the next batch if needed
    // This function can be expanded based on your requirements
    console.log('Analyzing next batch...');
}

// Call the function on page load
document.addEventListener('DOMContentLoaded', updateAnalysisInfo);












// dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    // Add event listeners to checkboxes
    document.getElementById('includeCheckbox').addEventListener('change', function () {
        updateCharts();
    });

    document.getElementById('excludeCheckbox').addEventListener('change', function () {
        updateCharts();
    });

    // Initial load with default decision values
    updateCharts();

    // Get the selected decision values based on checkbox states

    // Determine the decision value based on checkbox states
    function updateCharts() {
        // Get the state of checkboxes
        const includeChecked = document.getElementById('includeCheckbox').checked;
        const excludeChecked = document.getElementById('excludeCheckbox').checked;


        // Fetch data from the server based on the selected decision value
        fetch(`/filter?include=${includeChecked}&exclude=${excludeChecked}`)
            .then(response => response.json())
            .then(data => {
                console.log(data);

                // Access the filtered data directly (assuming it's an array)
                let filteredData = data;
                console.log(filteredData);

                // Chart 1: Bar chart between Include and Exclude and their total count
                let includeCount = filteredData.filter(item => item['ai_decision'] === 'Include').length;
                let excludeCount = filteredData.filter(item => item['ai_decision'] === 'Exclude').length;

                let chart1Data = [{
                    x: ['Include', 'Exclude'],
                    y: [includeCount, excludeCount],
                    type: 'bar',
                    text: [`${includeCount} Papers`, `${excludeCount} Papers`],
                    textposition: 'auto'
                }];

                // Layout settings
                let layout1 = {
                    title: "AI Decision Summary",
                    xaxis: {
                        title: 'Decision'
                    },
                    yaxis: {
                        title: 'Number of Evidences'
                    }
                };

                // Chart 2: Bar chart for Publication Year
                let publicationYears = filteredData.map(item => item['Publication Year']);
                let yearCounts = countOccurrences(publicationYears);

                let chart2Data = [{
                    x: Object.keys(yearCounts),
                    y: Object.values(yearCounts),
                    type: 'bar',
                    text: Object.values(yearCounts).map(count => `${count} Papers`),
                    textposition: 'auto'
                }];
                let layout2 = {
                    title: "Distribution of Evidences by years",
                    xaxis: {
                        title: 'Year'
                    },
                    yaxis: {
                        title: 'Number of Publications'
                    }
                };

                // Chart 3: Pie chart for Publication Type
                let publicationTypeCounts = countOccurrences(filteredData.map(item => item['Publication Type']));
                let chart3Data = [{
                    labels: Object.keys(publicationTypeCounts),
                    values: Object.values(publicationTypeCounts),
                    type: 'pie'
                }];
                let layout3 = {
                    title: "Types of Publications",

                };

                // Create Plotly charts
                Plotly.newPlot('chart1', chart1Data, layout1);
                Plotly.newPlot('chart2', chart2Data, layout2);
                Plotly.newPlot('chart3', chart3Data, layout3);

                // Additional code if needed...
            })
            .catch(error => console.error('Error fetching data:', error));
        function countOccurrences(arr) {
            return arr.reduce((acc, val) => {
                acc[val] = (acc[val] || 0) + 1;
                return acc;
            }, {});
        }
    }














    fetch('/get_metrics')
        .then(response => response.json())
        .then(data => {
            console.log(data);

            // Update the summary table elements
            data.data.summary_metrics.forEach(metric => {
                const metricElement = document.getElementById(metric.Metric.toLowerCase() + 'Value');
                if (metricElement) {
                    metricElement.innerHTML = metric.Value.toFixed(3);
                }
            });
            console.log(data.data.decision_metrics)

            // Update the decision metrics table elements
            const totalIncludedHuman = document.getElementById('totalIncludedHuman');
            const totalExcludedHuman = document.getElementById('totalExcludedHuman');
            const totalIncludedAI = document.getElementById('totalIncludedAI');
            const totalExcludedAI = document.getElementById('totalExcludedAI');
            const accuracyPercentage = document.getElementById('accuracyPercentage');
            const conflictingdecisionsInclude = document.getElementById('conflictingdecisionsInclude');
            const conflictingdecisionsExclude = document.getElementById('conflictingdecisionsExclude');
            const totalHuman = document.getElementById('totalHuman');
            const totalAI = document.getElementById('totalAI');
            const totalConflicts = document.getElementById('totalConflicts');

            totalIncludedHuman.innerHTML = data.data.decision_metrics.total_included_human;
            totalExcludedHuman.innerHTML = data.data.decision_metrics.total_excluded_human;
            totalIncludedAI.innerHTML = data.data.decision_metrics.total_included_ai;
            totalExcludedAI.innerHTML = data.data.decision_metrics.total_excluded_ai;
            conflictingdecisionsInclude.innerHTML = data.data.decision_metrics.conflicting_decisions_include;
            conflictingdecisionsExclude.innerHTML = data.data.decision_metrics.conflicting_decisions_exclude;
            totalAI.innerHTML = data.data.decision_metrics.totalAI;
            totalHuman.innerHTML = data.data.decision_metrics.totalHuman;
            totalConflicts.innerHTML = data.data.decision_metrics.totalConflicts;
            accuracyPercentage.innerHTML = data.data.decision_metrics.accuracy_percentage.toFixed(2) + '%';




            const exclusionReasonTableBody = document.getElementById('exclusionReasonTableBody');
            exclusionReasonTableBody.innerHTML = '';
            let grandTotal = 0;
            data.data.exclusion_reason_counts.forEach(reason => {
                const row = exclusionReasonTableBody.insertRow();
                row.insertCell(0).textContent = reason['Reason'];
                row.insertCell(1).textContent = reason['Count'];
                grandTotal += reason['Count'];
            });

            // Add grand total row


            // Populate grand total in the specified element
            const grandTotalElement = document.getElementById('grandTotal');
            if (grandTotalElement) {
                grandTotalElement.textContent = grandTotal;
            }







        })
        .catch(error => {
            console.error('Error:', error);

        });


    // Fetch data for the pie chart from FastAPI backend

});
// Function to toggle visibility of the metric table and update heading
function toggleMetricTable() {
    const metricTable = document.getElementById('metricTable');
    const heading = document.getElementById('metricTableHeading');
    const moreInfo = document.getElementById('moreInfo');

    if (metricTable.style.display === 'none') {
        // If metric table is hidden, show the table and update heading
        metricTable.style.display = 'table';
        heading.innerText = 'Metric Table';
        moreInfo.style.display = 'none';
    } else {
        // If metric table is visible, hide the table and update heading
        metricTable.style.display = 'none';
        heading.innerText = 'More Info';
        moreInfo.style.display = 'block';

    }
}


document.addEventListener('DOMContentLoaded', function () {
    // Get the "Upload Model" button
    var secondpass = document.getElementById('secondpass');

    // Add click event listener
    secondpass.addEventListener('click', function () {
        // Redirect to the "/upload" route
        // window.location.href = '/signin';
        window.location.href = '/secondpass';
    });
});

// // Event listener to toggle visibility when heading is clicked
// document.getElementById('metricTableHeading').addEventListener('click', toggleMetricTable);

// // Event listener to toggle visibility when heading is clicked
// document.getElementById('metricTableHeading').addEventListener('click', toggleMetricTable);


// document.getElementById('secondpass').addEventListener('click', function() {
//     // Make an AJAX request when the button is clicked
//     var xhr = new XMLHttpRequest();
    
//     // Define the request type, URL, and set it to asynchronous
//     xhr.open('GET', '/secondpass', true);

//     // Set up a callback function to handle the response
//     xhr.onload = function() {
//         if (xhr.status >= 200 && xhr.status < 300) {
//             // Successful response, redirect the user to secondpass.html
//             document.open();
//             document.write(xhr.responseText);
//             document.close();
//         } else {
//             // Error handling
//             console.error('Request failed with status ' + xhr.status);
//         }
//     };

//     // Send the request
//     xhr.send();
// });







function uploadPDF(title, index) {
    const fileInput = document.getElementById(`pdfUpload${index}`);
    const file = fileInput.files[0];
  
    if (file) {
      const formData = new FormData();
      formData.append('pdfFile', file);
  
      // Use fetch to send the PDF file to the FastAPI backend
      fetch('/upload-pdf', {
        method: 'POST',
        body: formData,
      })
        .then(response => response.json())
        .then(data => {
          console.log('Upload successful:', data);
  
          // Now you can use data.result for further processing
          const gptResult = data.result;
          // Implement your logic to use the GPT result
        })
        .catch(error => {
          console.error('Error uploading PDF:', error);
        });
    } else {
      console.error('No file selected for upload.');
    }
  }