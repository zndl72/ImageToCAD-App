// OpenSCAD Model of a Panzer IV-style Tank (Metal Earth style / stylized assembly)
// All measurements are parametric estimates based on typical proportions ($fn=32 for performance)

$fn = 32;

module tank() {
    // Colors
    steel = [0.45, 0.47, 0.5];
    dark_steel = [0.3, 0.32, 0.35];

    // --- CHASSIS / HULL ---
    color(steel)
    union() {
        // Lower Hull Body
        translate([0, 0, 8])
        cube([70, 36, 12], center=true);

        // Upper Hull (Sloped Front & Superstructure)
        translate([5, 0, 17])
        cube([60, 34, 7], center=true);

        // Front Glacis Plate detail
        translate([32, 0, 11])
        cube([8, 34, 6], center=true);

        // Fenders (Left and Right)
        translate([0, 20, 14])
        cube([80, 4, 1.5], center=true);
        translate([0, -20, 14])
        cube([80, 4, 1.5], center=true);
    }

    // --- TRACKS & WHEELS ---
    module track_side(y_offset) {
        // Track Base/Belt
        color(dark_steel)
        translate([0, y_offset, 6])
        hull() {
            translate([-32, 0, 0]) cylinder(r=6, h=10, center=true);
            translate([ 32, 0, 0]) cylinder(r=6, h=10, center=true);
        }

        // Road Wheels
        for (x = [-24, -14, -4, 6, 16, 26]) {
            color(steel)
            translate([x, y_offset + (y_offset > 0 ? 1 : -1), 6])
            rotate([90, 0, 0])
            cylinder(r=5.5, h=3, center=true);
        }

        // Drive Sprocket (Front)
        color(steel)
        translate([33, y_offset + (y_offset > 0 ? 1 : -1), 6])
        rotate([90, 0, 0])
        cylinder(r=6.2, h=4, center=true);

        // Idler Wheel (Rear)
        color(steel)
        translate([-33, y_offset + (y_offset > 0 ? 1 : -1), 6])
        rotate([90, 0, 0])
        cylinder(r=6, h=4, center=true);
    }

    track_side(19);
    track_side(-19);

    // --- TURRET ---
    color(steel)
    union() {
        // Turret Base / Ring
        translate([-2, 0, 22.5])
        cylinder(r=16, h=3, center=true);

        // Main Turret Box
        translate([-2, 0, 27])
        cube([30, 28, 10], center=true);

        // Turret Rear Baffle (Stowage bin)
        translate([-16, 0, 27])
        cube([8, 22, 9], center=true);

        // Commander's Cupola (cylindrical tower on top right/center)
        translate([-4, 4, 34])
        cylinder(r=6, h=6, center=true);
        
        // Cupola Hatch lid
        translate([-4, 4, 37.5])
        cylinder(r=6.5, h=1, center=true);
    }

    // --- MAIN GUN / BARREL ---
    color(steel)
    union() {
        // Mantlet
        translate([8, 0, 27])
        cube([8, 12, 10], center=true);

        // Barrel Base
        translate([15, 0, 27])
        rotate([0, 90, 0])
        cylinder(r=2.2, h=16, center=true);

        // Barrel Extension (Longer thin tube)
        translate([28, 0, 27])
        rotate([0, 90, 0])
        cylinder(r=1.5, h=14, center=true);

        // Muzzle Brake
        translate([37, 0, 27])
        rotate([0, 90, 0])
        cylinder(r=2, h=4, center=true);
    }
}

// Render the tank model
tank();