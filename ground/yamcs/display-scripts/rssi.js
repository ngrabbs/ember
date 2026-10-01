importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var value = PVUtil.getLong(pvs[0]);
widget.setPropertyValue("text", value === -32768 ? "Unavailable" : value + " dBm");
