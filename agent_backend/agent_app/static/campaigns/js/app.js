document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    const clearAllBtn = document.getElementById('clearAllBtn');
    const filterCountEl = document.getElementById('filterCount');
    const readyIndicator = document.getElementById('readyIndicator');
    const resultsArea = document.getElementById('resultsArea');
    const resultsMessage = document.getElementById('resultsMessage');
    const leadCountEl = document.getElementById('leadCount');
    const leadsListEl = document.getElementById('leadsList');
    
    flatpickr('#from_date', {
        dateFormat: 'F j, Y',
        onChange: updateFilterCount
    });
    
    flatpickr('#to_date', {
        dateFormat: 'F j, Y',
        onChange: updateFilterCount
    });
    
    if (!filterForm) {
        return; // Page without the form; exit safely
    }
    
    const formInputs = filterForm.querySelectorAll('input, select');
    formInputs.forEach(input => {
        input.addEventListener('change', updateFilterCount);
        input.addEventListener('input', updateFilterCount);
    });
    
    function getElValue(id) {
        const el = document.getElementById(id);
        return el ? el.value : '';
    }
    
    function updateFilterCount() {
        let count = 0;
        
        const project = getElValue('project_name');
        if (project) count++;
        
        const minBudget = getElValue('min_budget');
        const maxBudget = getElValue('max_budget');
        if (minBudget || maxBudget) count++;
        
        const unitTypes = document.querySelectorAll('input[name="unit_type"]:checked');
        if (unitTypes.length > 0) count++;
        
        const leadStatuses = document.querySelectorAll('input[name="lead_status"]:checked');
        if (leadStatuses.length > 0) count++;
        
        const fromDate = getElValue('from_date');
        const toDate = getElValue('to_date');
        if (fromDate || toDate) count++;
        
        filterCountEl.textContent = count;
        
        if (count > 0) {
            readyIndicator.style.display = 'flex';
        } else {
            readyIndicator.style.display = 'none';
        }
    }
    
    // Validate minimum 2 filters before submit
    filterForm.addEventListener('submit', function(e) {
        let count = 0;
        const project = getElValue('project_name');
        if (project) count++;
        const minBudget = getElValue('min_budget');
        const maxBudget = getElValue('max_budget');
        if (minBudget || maxBudget) count++;
        const unitTypes = document.querySelectorAll('input[name="unit_type"]:checked');
        if (unitTypes.length > 0) count++;
        const leadStatuses = document.querySelectorAll('input[name="lead_status"]:checked');
        if (leadStatuses.length > 0) count++;
        const fromDate = getElValue('from_date');
        const toDate = getElValue('to_date');
        if (fromDate || toDate) count++;

        const formError = document.getElementById('formError');
        if (count < 2) {
            e.preventDefault();
            if (formError) {
                formError.textContent = 'Please select at least 2 filters before shortlisting.';
                formError.style.display = 'block';
            }
            return false;
        } else if (formError) {
            formError.textContent = '';
            formError.style.display = 'none';
        }
        return true;
    });
    
    function displayResults(data) {
        if (resultsArea) resultsArea.style.display = 'block';
        if (leadCountEl && data && typeof data.count !== 'undefined') {
            leadCountEl.textContent = data.count;
        }
        
        if (leadsListEl) {
            leadsListEl.innerHTML = '';
        }
        
        if (data.leads && data.leads.length > 0) {
            data.leads.forEach(lead => {
                const leadCard = document.createElement('div');
                leadCard.className = 'lead-card';
                leadCard.innerHTML = `
                    <h4>${lead.name}</h4>
                    <p><strong>Email:</strong> ${lead.email}</p>
                    <p><strong>Phone:</strong> ${lead.phone}</p>
                    <p><strong>Project:</strong> ${lead.project}</p>
                    <p><strong>Budget:</strong> $${lead.budget.toLocaleString()}</p>
                    <p><strong>Unit Type:</strong> ${lead.unit_type}</p>
                    <p><strong>Status:</strong> ${lead.visit_status}</p>
                `;
                if (leadsListEl) {
                    leadsListEl.appendChild(leadCard);
                }
            });
        }
        
        if (resultsArea) {
            resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    clearAllBtn.addEventListener('click', function() {
        filterForm.reset();
        updateFilterCount();
        resultsArea.style.display = 'none';
    });
    
    updateFilterCount();
});
