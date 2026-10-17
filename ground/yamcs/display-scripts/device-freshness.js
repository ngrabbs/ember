importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var known = PVUtil.getTimeInMilliseconds(pvs[0]) > 0;
var expired = PVUtil.getSeverity(pvs[0]) < 0;
widget.setPropertyValue("text", !known ? "NO DISCOVERY SNAPSHOT" : expired ? "SNAPSHOT EXPIRED — current device health unknown" : "SNAPSHOT CURRENT — states and ages were sampled by IHU");
