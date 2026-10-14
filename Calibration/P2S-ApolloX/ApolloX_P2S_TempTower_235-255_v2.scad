// ApolloX temperature tower v2 - all temperature numbers physically attached
$fn=48;
FONT="Liberation Sans:style=Bold";
OVERLAP=0.15;

module side_label(txt,z,size=3.5,h=0.55){
    // Right side wall x=24 is solid; overlap by 0.15 mm into the tower.
    translate([24-OVERLAP,12,z])
        rotate([90,0,90])
        linear_extrude(height=h+OVERLAP)
        text(txt,size=size,halign="center",valign="center",font=FONT);
}

module seg(z,txt){
    union(){
        difference(){
            translate([0,0,z]) cube([24,24,8]);
            translate([4,-1,z+2]) cube([16,26,4]);
            translate([7,4,z-1]) cube([10,16,10]);
        }
        side_label(txt,z+4);
    }
}

union(){
    cube([24,24,2]);
    seg(2,"255");
    seg(10,"250");
    seg(18,"245");
    seg(26,"240");
    seg(34,"235");
}
