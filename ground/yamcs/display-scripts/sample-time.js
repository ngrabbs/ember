importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
// Generation time is ground reception time, including in archive replay.
var ms = PVUtil.getTimeInMilliseconds(pvs[0]);
widget.setPropertyValue("text", ms > 0 ? new Date(ms).toISOString().replace("T", " ").replace("Z", " UTC") : "No sample received");
