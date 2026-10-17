importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var expired = PVUtil.getSeverity(pvs[0]) < 0;
widget.setPropertyValue("text", expired ? "SNAPSHOT EXPIRED / unavailable — rows are historical, not current device health" : "Registry snapshot received — device states and ages are sampled by IHU");
