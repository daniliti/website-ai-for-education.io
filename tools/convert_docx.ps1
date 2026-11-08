param(
  [Parameter(Mandatory=$true)][string]$InPath,
  [Parameter(Mandatory=$true)][string]$OutPath
)
$ErrorActionPreference = 'Stop'
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
$doc = $w.Documents.Open($InPath)
try {
  $doc.Fields.Update() | Out-Null
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
  $doc.Repaginate()
  $doc.Save()
  $doc.ExportAsFixedFormat($OutPath, 17)
  Write-Output "converted: $OutPath"
} finally {
  $doc.Close()
  $w.Quit()
}
