$baseUrl = "http://localhost:5000/api"

function Test-Endpoint {
    param (
        [string]$endpoint,
        [string]$description,
        [string]$method = "Get",
        $body = $null,
        [switch]$suppressOutput
    )
    Write-Host "`n====== Testing $description ======" -ForegroundColor Cyan
    try {
        $params = @{
            Uri = "$baseUrl/$endpoint"
            Method = $method
            ContentType = "application/json"
        }
        if ($body) {
            $params.Body = $body | ConvertTo-Json
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "Status: Success" -ForegroundColor Green
        if (-not $suppressOutput) {
            Write-Host "Response Data:"
            $response | ConvertTo-Json -Depth 10
        }
        return $response
    }
    catch {
        Write-Host "Status: Failed" -ForegroundColor Red
        Write-Host "Error: $_"
        return $null
    }
    finally {
        Write-Host "==============================`n" -ForegroundColor Cyan
    }
}

# Test getting firefighters
Test-Endpoint -endpoint "firefighters" -description "Get All Firefighters"

# Add new firefighter with correct data structure
$newFirefighter = @{
    badge_number = "123470"
    first_name = "Test"
    last_name = "Firefighter"
}

$createdFirefighter = Test-Endpoint -endpoint "firefighters" -description "Create New Firefighter" -method "Post" -body $newFirefighter

if ($createdFirefighter) {
    # Create BA Entry for the firefighter
    $baEntry = @{
        firefighter_id = $createdFirefighter.id
        initial_pressure = 280
        location = "Test Location"
        remarks = "Test Entry"
    }

    $createdEntry = Test-Endpoint -endpoint "ba-entries" -description "Create BA Entry" -method "Post" -body $baEntry

    if ($createdEntry) {
        # Update BA Entry pressure
        Start-Sleep -Seconds 2  # Wait a bit to show time difference
        $updateData = @{
            current_pressure = 260
        }

        Test-Endpoint -endpoint "ba-entries/$($createdEntry.id)" -description "Update BA Entry Pressure" -method "Put" -body $updateData
    }

    # Test firefighter analysis
    Test-Endpoint -endpoint "firefighters/$($createdFirefighter.id)/analyze" -description "Analyze Firefighter" -method "Post"

    # Test time predictions
    Test-Endpoint -endpoint "firefighters/$($createdFirefighter.id)/predictions/280" -description "Get Time Predictions"
}

# Get active BA entries
Test-Endpoint -endpoint "ba-entries?active=true" -description "Get Active BA Entries"

# Get historical entries
Test-Endpoint -endpoint "historical" -description "Get Historical Entries"

# Test low pressure scenario
if ($createdEntry) {
    Start-Sleep -Seconds 2  # Wait a bit to show time difference
    $lowPressureData = @{
        current_pressure = 145
    }

    Write-Host "`n====== Testing Low Pressure Scenario ======" -ForegroundColor Yellow
    Test-Endpoint -endpoint "ba-entries/$($createdEntry.id)" -description "Update to Low Pressure" -method "Put" -body $lowPressureData

    # Verify entry moved to historical
    Test-Endpoint -endpoint "historical" -description "Verify Historical Entry Created"
    Test-Endpoint -endpoint "ba-entries?active=true" -description "Verify Entry No Longer Active"
}

# Test data summary
Write-Host "`n====== Final System State ======" -ForegroundColor Green
Write-Host "Testing individual endpoints:"
Write-Host "1. Active Firefighters:"
Test-Endpoint -endpoint "firefighters" -description "All Firefighters"

Write-Host "`n2. Active BA Entries:"
Test-Endpoint -endpoint "ba-entries?active=true" -description "Active BA Entries"

Write-Host "`n3. Historical Records:"
Test-Endpoint -endpoint "historical" -description "Historical Entries"

Write-Host "`nTest script completed" -ForegroundColor Green