param([string]$Pdf,[int]$Page,[string]$Out)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null=[Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null=[Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null=[Windows.Storage.Streams.DataReader,Windows.Storage.Streams,ContentType=WindowsRuntime]
$asTask=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1)
function Await($Operation,[Type]$ResultType) {
 $task=$asTask.MakeGenericMethod($ResultType).Invoke($null,@($Operation))
 $task.Wait()
 return $task.Result
}
$file=Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Pdf)) ([Windows.Storage.StorageFile])
$doc=Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
$pdfPage=$doc.GetPage($Page-1)
$stream=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
$action=$pdfPage.RenderToStreamAsync($stream)
$actionMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1
$task=$actionMethod.Invoke($null,@($action))
$task.Wait()
$stream.Seek(0)
$reader=New-Object Windows.Storage.Streams.DataReader($stream)
$null=Await ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
$bytes=New-Object byte[] ([int]$stream.Size)
$reader.ReadBytes($bytes)
[IO.File]::WriteAllBytes($Out,$bytes)
$reader.Dispose();$stream.Dispose();$pdfPage.Dispose()
Write-Output $Out
