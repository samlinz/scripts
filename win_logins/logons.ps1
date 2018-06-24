#Requires -RunAsAdministrator

# Create CSV of Windows logons

param([int]$number=100)
$regex = "(?m)^\s*Account Name:\s+(\S+)\$"

echo "Fetching logons from event log"

$logins = Get-WinEvent -LogName Security -MaxEvents ($number*10) `
    | Where-Object {$_.Message -match "An account was successfully logged on." } `
    | Sort-Object {$_.TimeCreated} -Descending `
    | Select -first $number
echo "Done"

$login_objs = @()

foreach ($login in $logins) {
    $matches = $login.Message | Select-String -Pattern $regex
    $name = $matches.Matches[0].Groups[1].Value
    $login_objs += New-Object -TypeName psobject -Property @{name=$name; time=$login.TimeCreated}
}

echo "Creating csv"

$filename = "logins_"
$date = get-date -format "yyyy-MM-dd-HHmmss"

$root = (Get-Location).Path
$fullpath = "$root\\$filename$date.csv"

Add-Content -Path $fullpath -Value '"Name","Time"'
foreach ($login in $login_objs) {
    $login | Export-Csv -Path $fullpath -Append -NoTypeInformation
}