importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var time = PVUtil.getTimeInMilliseconds(pvs[0]);
// These packet definitions have no expiry. Acquisition status is not liveness.
widget.setPropertyValue("text", !(time > 0) ? "NO OBSERVATION" : PVUtil.getSeverity(pvs[0]) < 0 ? "UNAVAILABLE" : "LAST RECEIVED · CHECK TIME");
