importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
// Bench generation time is Yamcs reception time, not spacecraft UTC.
var ms = PVUtil.getTimeInMilliseconds(pvs[0]);
widget.setPropertyValue("text", ms ? new Date(ms).toISOString().replace("T", " ").replace("Z", " UTC") : "No sample received");
