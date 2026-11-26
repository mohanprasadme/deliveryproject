# Converts old .doc files in a folder to .docx using Microsoft Word (must be installed).
# Usage (PowerShell):  .\convert_doc_to_docx.ps1 -Folder "C:\OldDC"
param([Parameter(Mandatory=$true)][string]$Folder)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
Get-ChildItem -Path $Folder -Filter *.doc -Recurse | Where-Object { $_.Extension -eq ".doc" } | ForEach-Object {
    $out = [System.IO.Path]::ChangeExtension($_.FullName, ".docx")
    if (-not (Test-Path $out)) {
        $doc = $word.Documents.Open($_.FullName, $false, $true)
        $doc.SaveAs2($out, 16)   # 16 = .docx
        $doc.Close($false)
        Write-Host "Converted $($_.Name)"
    }
}
$word.Quit()
