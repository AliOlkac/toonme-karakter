"""Windows bildirimleri (PowerShell üzerinden, ek paket gerektirmeden)."""
import base64
import logging
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from .adb import PENCERESIZ

log = logging.getLogger(__name__)

POWERSHELL_AUMID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"


def toast_xml(baslik: str, metin: str, acilacak: Path | None = None) -> str:
    acilis = f' activationType="protocol" launch={quoteattr(acilacak.as_uri())}' if acilacak else ""
    return (f"<toast{acilis}><visual><binding template=\"ToastGeneric\">"
            f"<text>{escape(baslik)}</text><text>{escape(metin)}</text>"
            f"</binding></visual></toast>")


def goster(baslik: str, metin: str, acilacak: Path | None = None) -> None:
    # XML base64 ile taşınır; böylece dosya adındaki tırnak/özel karakterler PowerShell'i bozamaz
    xml64 = base64.b64encode(toast_xml(baslik, metin, acilacak).encode("utf-8")).decode("ascii")
    betik = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] > $null;"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] > $null;"
        "$d = New-Object Windows.Data.Xml.Dom.XmlDocument;"
        f"$d.LoadXml([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{xml64}')));"
        "$t = New-Object Windows.UI.Notifications.ToastNotification $d;"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{POWERSHELL_AUMID}').Show($t)"
    )
    kodlu = base64.b64encode(betik.encode("utf-16-le")).decode("ascii")
    try:
        subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-EncodedCommand", kodlu],
                       capture_output=True, timeout=30, creationflags=PENCERESIZ)
    except Exception as h:
        log.warning("Bildirim gösterilemedi: %s", h)
