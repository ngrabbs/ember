importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var expired = PVUtil.getSeverity(pvs[0]) < 0;
var valid = PVUtil.getLong(pvs[0]) === 1;
var conversion = PVUtil.getLong(pvs[1]) === 1;
var link = PVUtil.getString(pvs[2]);
widget.setPropertyValue("text", expired ? "STALE — no current EPS packet" : !valid ? link + " — readout unavailable" : conversion ? link + " — readout and ADC conversion valid" : link + " — ADC or cell configuration invalid");
