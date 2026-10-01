importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var expired = PVUtil.getSeverity(pvs[0]) < 0;
var valid = PVUtil.getLong(pvs[0]) === 1;
widget.setPropertyValue("text", expired ? "STALE / no current EPS packet — readings unknown" : valid ? "UART READOUT VALID — see conversion quality and raw status below" : "NO VALID CURRENT READOUT — readings unavailable; inspect EPS raw / quality");
