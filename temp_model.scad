// OpenSCAD Catapult Model

// Global parameters
$fn = 32;

// Colors
wood_color = [0.72, 0.45, 0.20];
dark_wood = [0.55, 0.32, 0.12];
rope_color = [0.90, 0.88, 0.75];

module wheel() {
    color(wood_color)
    rotate([0, 90, 0])
    union() {
        // Main disc
        cylinder(h=8, r=35, center=true);
        // Rim details / concentric rings
        color(dark_wood)
        difference() {
            cylinder(h=9, r=32, center=true);
            cylinder(h=10, r=26, center=true);
        }
        // Center hub
        color(dark_wood)
        cylinder(h=11, r=12, center=true);
        color(wood_color)
        cylinder(h=12, r=6, center=true);
    }
}

module catapult() {
    // === BASE FRAME ===
    // Horizontal main beams (two parallel beams along X axis)
    color(wood_color)
    for (z = [-15, 15]) {
        translate([-90, z, -5])
        cube([190, 8, 10], center=true);
    }
    
    // Front and rear crossbars
    color(wood_color) {
        translate([-85, 0, -5])
        cube([8, 38, 10], center=true);
        
        translate([90, 0, -5])
        cube([8, 38, 10], center=true);
    }

    // === WHEELS ===
    translate([-85, 25, -5]) wheel();
    translate([-85, -25, -5]) wheel();
    translate([90, 25, -5]) wheel();
    translate([90, -25, -5]) wheel();

    // === A-FRAME TOWER ===
    // Vertical center post
    color(wood_color)
    translate([10, 0, 45])
    cube([10, 10, 100], center=true);

    // Diagonal braces forming the 'A' frame (viewed from side, centered around X=10, Z=45)
    // Left diagonals (pointing to top of vertical post and base ends)
    color(wood_color) {
        // Front diagonal strut
        hull() {
            translate([10, 0, 90]) cube([6, 6, 6], center=true);
            translate([-50, 0, -5]) cube([6, 16, 6], center=true);
        }
        // Rear diagonal strut
        hull() {
            translate([10, 0, 90]) cube([6, 6, 6], center=true);
            translate([70, 0, -5]) cube([6, 16, 6], center=true);
        }
    }

    // === TENSION WINCH / DRUM (Center mechanism with spokes) ===
    color(dark_wood)
    translate([10, 0, 0])
    rotate([0, 90, 0])
    union() {
        cylinder(h=22, r=16, center=true);
        // Spokes/teeth around the winch
        for (i = [0 : 11]) {
            rotate([0, 0, i * 30])
            translate([18, 0, 0])
            cube([6, 3, 20], center=true);
        }
    }

    // === THROWING ARM ===
    color(wood_color)
    translate([0, 0, 0])
    rotate([0, -18, 0])
    union() {
        // Main long beam extending from back to front bucket
        translate([-30, 0, 0])
        cube([220, 12, 16], center=true);

        // Sling / Bucket at the front end
        translate([-135, 0, 18])
        color(dark_wood)
        intersection() {
            // Scoop shape
            translate([0, 0, 10])
            sphere(r=25);
            // Trim to make a bucket/spoon
            translate([0, 0, 25])
            cube([50, 40, 50], center=true);
        }
        
        // Rope wrapping near the bucket attachment
        color(rope_color)
        translate([-110, 0, 5])
        rotate([0, 90, 0])
        cylinder(h=15, r=8, center=true);
    }
}

// Render the complete assembly
catapult();