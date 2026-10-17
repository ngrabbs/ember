importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var time = PVUtil.getTimeInMilliseconds(pvs[0]);
widget.setPropertyValue("text", !(time > 0) ? "NO OBSERVATION" : PVUtil.getSeverity(pvs[0]) < 0 ? "EXPIRED / UNAVAILABLE" : "PACKET CURRENT");
