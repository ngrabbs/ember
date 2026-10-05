importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var age = PVUtil.getLong(pvs[0]);
widget.setPropertyValue("text", PVUtil.getSeverity(pvs[0]) < 0 ? "EPS packet expired; EPS readout age unknown" : age === 4294967295 ? "No complete PEC-checked EPS readout received" : "Last good EPS readout: " + (age / 1000).toFixed(1) + " s before this packet • repeats are not new ADC samples");
