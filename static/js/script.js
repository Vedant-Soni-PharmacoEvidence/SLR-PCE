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
            window.location.href="/dashboard"
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














// dashboard.js

document.addEventListener("DOMContentLoaded", function () {
    // Fetch data for the bar graph from FastAPI backend
    fetch('/get_publications_by_year_and_type')
        .then(response => response.json())
        .then(data => {
            // Prepare data for the bar graph
            const barGraphData = prepareBarGraphData(data.publications_by_year);

            // Create Plotly bar graph
            Plotly.newPlot('plotlyGraphContainer', barGraphData, {});

            // Create checkboxes for years
            createYearCheckboxes(data.publications_by_year.map(entry => entry['Publication Year']));
        })
        .catch(error => {
            console.error('Error fetching bar graph data:', error);
        });

    fetch('/get_metrics')
        .then(response => response.json())
        .then(data => {
            console.log(data);
    
            // Update the summary table elements
            data.data.summary_metrics.forEach(metric => {
                const metricElement = document.getElementById(metric.Metric.toLowerCase() + 'Value');
                if (metricElement) {
                    metricElement.innerHTML = metric.Value .toFixed(3);
                }
            });
    
            // Update the decision metrics table elements
            const totalIncludedHuman = document.getElementById('totalIncludedHuman');
            const totalExcludedHuman = document.getElementById('totalExcludedHuman');
            const totalIncludedAI = document.getElementById('totalIncludedAI');
            const totalExcludedAI = document.getElementById('totalExcludedAI');
            
            const accuracyPercentage = document.getElementById('accuracyPercentage');
            const conflictingdecisions= document.getElementById('conflictingdecisions');
    
            if (totalIncludedHuman && totalExcludedHuman && totalIncludedAI && totalExcludedAI && conflictingdecisions && accuracyPercentage ) {
                totalIncludedHuman.innerHTML = data.data.decision_metrics.total_included_human;
                totalExcludedHuman.innerHTML = data.data.decision_metrics.total_excluded_human;
                totalIncludedAI.innerHTML = data.data.decision_metrics.total_included_ai;
                totalExcludedAI.innerHTML = data.data.decision_metrics.total_excluded_ai;
                conflictingdecisions.innerHTML=data.data.decision_metrics.conflicting_decisions;
                accuracyPercentage.innerHTML =data.data.decision_metrics.accuracy_percentage.toFixed(2) + '%';
                
                
            }
            const exclusionReasonTableBody = document.getElementById('exclusionReasonTableBody');
        exclusionReasonTableBody.innerHTML = '';
        let grandTotal = 0;
        data.data.exclusion_reason_counts.forEach(reason => {
            const row = exclusionReasonTableBody.insertRow();
            row.insertCell(0).textContent = reason['Exclusion Reason'];
            row.insertCell(1).textContent = reason['Count'];
            grandTotal += reason['Count'];
        });

        // Add grand total row
        

        // Populate grand total in the specified element
        const grandTotalElement = document.getElementById('grandTotal');
        if (grandTotalElement) {
            grandTotalElement.textContent = grandTotal;
        }




        const aiDecisionData = data.data.ai_decision_data;

        if (aiDecisionData.length > 0) {
            const labels = aiDecisionData.map(entry => entry.ai_decision);
            const counts = aiDecisionData.map(entry => entry.count);

            const dataTrace = {
                x: labels,
                y: counts,
                type: 'bar',
                
            };

            const layout = {
                title: 'AI Decision Counts',
                xaxis: { title: 'Decision' },
                yaxis: { title: 'Count' }
            };

            Plotly.newPlot('aiDecisionChart', [dataTrace], layout);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching metrics. Please try again.');
    });
    
    
    // Fetch data for the pie chart from FastAPI backend
    fetch('/get_publications_by_year_and_type?type=true')
        .then(response => response.json())
        .then(data => {
            // Create checkboxes for types
            createTypeCheckboxes(data.publications_by_type);

            // Initialize the pie chart with all available types
            updatePieChart();
        })
        .catch(error => {
            console.error('Error fetching pie chart data:', error);
        });
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

// Event listener to toggle visibility when heading is clicked
document.getElementById('metricTableHeading').addEventListener('click', toggleMetricTable);

// Event listener to toggle visibility when heading is clicked
document.getElementById('metricTableHeading').addEventListener('click', toggleMetricTable);
function prepareBarGraphData(data) {
    // Create an array of unique colors for each year
    const uniqueColors = Array.from({ length: data.length }, (_, index) => `rgb(${index * 30}, ${index * 20 + 50}, ${index * 10 + 100})`);



    
    // Convert data to Plotly format for bar graph
    const barGraphData = data.map((entry, index) => ({
        x: [entry['Publication Year']],
        y: [entry['Count']],
        type: 'bar',
        name: entry['Publication Year'].toString(),
        hoverinfo: 'y+name',
        
    }));

    // Layout settings to customize axis labels and legend
    const layout = {
        xaxis: {
            title: 'Publication Year',
             // Set the step to 1 for a proper 1-step scale
        },
        yaxis: {
            title: 'Publication Count',
        },
        legend: {
            traceorder: 'reversed',
        },
        marker: {
            color: 'blue',  // Set the color to blue
        },
    };
    return { data: barGraphData, layout: layout };
}


function createYearCheckboxes(years) {
    const checkboxesContainer = document.getElementById('yearCheckboxes');

    years.forEach(year => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `year${year}`;
        checkbox.checked = true;  // Initially, all checkboxes are checked
        checkbox.addEventListener('change', updateGraph);

        const label = document.createElement('label');
        label.htmlFor = `year${year}`;
        label.textContent = year;

        checkboxesContainer.appendChild(checkbox);
        checkboxesContainer.appendChild(label);
    });
}

function createTypeCheckboxes(types) {
    const checkboxContainer = document.getElementById('typeCheckboxes');

    types.forEach(type => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `type${type['Publication Type']}`;
        checkbox.className = 'type-checkbox';
        checkbox.checked = true;  // Initially, all checkboxes are checked
        checkbox.addEventListener('change', updatePieChart);

        const label = document.createElement('label');
        label.htmlFor = `type${type['Publication Type']}`;
        label.textContent = type['Publication Type'];

        checkboxContainer.appendChild(checkbox);
        checkboxContainer.appendChild(label);
    });
}

function updateGraph() {
    // Get selected years
    const selectedYears = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.id.replace('year', ''));

    // Fetch data for the bar graph based on selected years from FastAPI backend
    fetch(`/get_publications_by_year_and_type?selected_years=${selectedYears.join(',')}`)
        .then(response => response.json())
        .then(data => {
            // Prepare data for the bar graph
            const barGraphData = prepareBarGraphData(data.publications_by_year);

            // Clear existing graph
            Plotly.purge('plotlyGraphContainer');

            // Initialize new bar graph with the updated data
            Plotly.newPlot('plotlyGraphContainer', barGraphData, {});
        })
        .catch(error => {
            console.error('Error fetching bar graph data:', error);
        });
}

function updatePieChart() {
    // Get selected types
    const selectedTypes = Array.from(document.querySelectorAll('.type-checkbox:checked'))
        .map(checkbox => checkbox.nextSibling.textContent);

    // Fetch data for the pie chart based on selected types from FastAPI backend
    fetch(`/get_publications_by_year_and_type?selected_types=${selectedTypes.join(',')}&type=true`)
        .then(response => response.json())
        .then(data => {
            // Prepare data for Plotly pie chart
            const pieData = preparePlotlyData(data.publications_by_type);

            // Check if a Plotly pie chart is already initialized
            const plotPublicationType = document.getElementById('plotPublicationType');
            if (plotPublicationType.data && plotPublicationType.data.length > 0) {
                // Update existing pie chart
                Plotly.update('plotPublicationType', pieData.data, pieData.layout);
            } else {
                // Initialize new pie chart
                Plotly.newPlot('plotPublicationType', pieData.data, pieData.layout);
            }
        })
        .catch(error => {
            console.error('Error fetching pie chart data:', error);
        });
}

function preparePlotlyData(data) {
    // Convert data to Plotly format for pie chart
    const pieData = [{
        labels: data.map(entry => entry['Publication Type']),
        values: data.map(entry => entry['Count']),
        type: 'pie',
    }];

    return { data: pieData, layout: { title: 'Publication Types' } };
}


