importPackage(Packages.org.csstudio.opibuilder.scriptUtil);
var sha = "", known = true;
for (var i=0;i<5;i++) {
    known = known && PVUtil.getTimeInMilliseconds(pvs[i]) > 0;
    var h=Number(PVUtil.getDouble(pvs[i])).toString(16);
    sha += ("00000000"+h).slice(-8);
}
widget.setPropertyValue("text", known ? sha : "No identity received");
