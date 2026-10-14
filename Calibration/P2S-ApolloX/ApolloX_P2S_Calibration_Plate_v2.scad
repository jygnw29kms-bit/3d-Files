// ApolloX P2S Calibration Plate v2 - labels physically attached
// Printer: Bambu Lab P2S, 0.4 mm nozzle
// Material: FormFutura ApolloX ASA, Blue
// Design rule: every label overlaps its parent solid by >= 0.15 mm.
// Units: mm
$fn=48;

FONT="Liberation Sans:style=Bold";
LABEL_OVERLAP=0.15;

// Horizontal embossed label. z_surface is the parent's top surface.
module label_top(txt, x, y, z_surface, size=4, h=0.55, rot=0){
    translate([x,y,z_surface-LABEL_OVERLAP])
        rotate([0,0,rot])
        linear_extrude(height=h+LABEL_OVERLAP)
        text(txt,size=size,halign="center",valign="center",font=FONT);
}

// Raised label on a front face located at y_face.
// Extrusion crosses the face: starts 0.15 mm inside parent and projects outward.
module label_front(txt, x, y_face, z, size=3.2, h=0.55){
    translate([x,y_face+LABEL_OVERLAP,z])
        rotate([90,0,0])
        linear_extrude(height=h+LABEL_OVERLAP)
        text(txt,size=size,halign="center",valign="center",font=FONT);
}

module first_layer_patch(x,y,txt){
    // Coupon itself: two 0.2 mm layers.
    translate([x,y,0.2]) cube([24,24,0.4],center=true);
    // Letter is embossed into the top with 0.15 mm overlap, so it cannot float.
    label_top(txt,x,y,0.4,4.0,0.35);
}

module wall_box(x,y){
    union(){
        difference(){
            translate([x,y,0]) cube([32,32,20],center=false);
            translate([x+1.2,y+1.2,1.0]) cube([29.6,29.6,20],center=false);
        }
        // Front face = y. The label crosses this wall by LABEL_OVERLAP.
        label_front("WALL 1.2",x+16,y,7,3.2,0.5);
    }
}

module dimensional_coupon(x,y){
    union(){
        difference(){
            translate([x,y,0]) cube([54,34,8],center=false);
            for(p=[[8,17,3],[20,17,5],[34,17,8],[47,17,10]])
                translate([x+p[0],y+p[1],-1]) cylinder(h=10,d=p[2]);
            translate([x+5,y+4,-1]) cube([20,3,10]);
            translate([x+29,y+4,-1]) cube([20,5,10]);
        }
        label_front("HOLES 3 5 8 10",x+27,y,4.0,3.0,0.5);
    }
}

module stringing_test(x,y){
    union(){
        // Thin common foot only at the base. It does not alter the stringing gap above Z=1.2.
        translate([x-3,y-5,0]) cube([46,10,1.2]);
        for(dx=[0,20,40]){
            translate([x+dx,y,0]) cylinder(h=35,d=6);
            translate([x+dx,y,35]) cylinder(h=4,d1=6,d2=2);
        }
        label_top("STRING",x+20,y-2.2,1.2,3.0,0.45);
    }
}

module bridge_pair(x,y,span,z){
    w=6;
    union(){
        translate([x,y,0]) cube([w,10,z]);
        translate([x+w+span,y,0]) cube([w,10,z]);
        translate([x,y,z]) cube([2*w+span,10,1.2]);
    }
}

module bridge_test(x,y){
    union(){
        bridge_pair(x,y,10,10);
        bridge_pair(x,y+16,20,14);
        bridge_pair(x,y+32,30,18);
        bridge_pair(x,y+48,40,22);
        // Attached identification strip touches/overlaps first bridge tower by 0.5 mm.
        translate([x,y-6,0]) cube([28,6.5,1.2]);
        label_top("BRIDGE 10-40",x+14,y-3,1.2,2.6,0.45);
    }
}

module overhang_step_tower(x,y){
    base=18;
    union(){
        translate([x,y,0]) cube([base,base,4]);
        for(i=[1:5]){
            off=(i-1)*2.0;
            translate([x-off,y,4+(i-1)*4]) cube([base+2*off,base,4]);
        }
        label_front("OVERHANG",x+9,y,2.1,2.7,0.5);
    }
}

module temp_segment(z,txt){
    union(){
        difference(){
            translate([0,0,z]) cube([24,24,8]);
            translate([4,-1,z+2]) cube([16,26,4]);
            translate([7,4,z-1]) cube([10,16,10]);
        }
        // The front face contains the calibration window, so labels must NOT be placed there.
        // Use the solid right side wall (x=24).  rotate([90,0,90]) maps the text plane
        // to Y/Z and extrusion to +X.  Starting at x=24-0.15 gives real material overlap.
        translate([24-LABEL_OVERLAP,12,z+4])
            rotate([90,0,90])
            linear_extrude(height=0.55+LABEL_OVERLAP)
            text(txt,size=3.5,halign="center",valign="center",font=FONT);
    }
}

module temp_tower(x,y){
    translate([x,y,0]) union(){
        cube([24,24,2]);
        temp_segment(2,"255");
        temp_segment(10,"250");
        temp_segment(18,"245");
        temp_segment(26,"240");
        temp_segment(34,"235");
        // Overall tower label is on the base top, not a free-standing side label.
        label_top("TEMP",12,12,2,3.0,0.45);
    }
}

module xy_cube(x,y){
    union(){
        translate([x,y,0]) cube([20,20,20]);
        label_front("20mm XYZ",x+10,y,7,2.8,0.5);
    }
}

module thin_walls(x,y){
    th=[0.42,0.84,1.26];
    union(){
        for(i=[0:2]){
            t=th[i];
            translate([x+i*18,y,0]) difference(){
                cube([14,28,16]);
                translate([t,t,1]) cube([14-2*t,28-2*t,16]);
            }
        }
        // Common identification strip overlaps all front walls only in bottom 1.2 mm.
        translate([x,y-6,0]) cube([50,6.5,1.2]);
        label_top("WALL FLOW",x+25,y-3,1.2,2.8,0.45);
    }
}

// Layout
first_layer_patch(-78,-82,"A");
first_layer_patch(-45,-82,"B");
first_layer_patch(-12,-82,"C");
dimensional_coupon(18,-94);

wall_box(-92,-42);
thin_walls(-45,-42);
stringing_test(20,-30);
temp_tower(72,-42);

bridge_test(-92,12);
overhang_step_tower(-18,22);
xy_cube(22,28);

// Title tag: text overlaps tag by 0.15 mm.
union(){
    translate([25,72,0]) cube([68,18,0.8]);
    label_top("APOLLOX P2S 0.4",59,81,0.8,4.0,0.55);
}
