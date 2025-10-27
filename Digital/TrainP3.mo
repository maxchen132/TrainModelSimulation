package TrainP3
model WagonAlongPath
  import Modelica.Math.Vectors.length;
  import Modelica.Math.Vectors.normalize;
  import Modelica.Blocks.Interfaces;
  import Modelica.Blocks.Tables.CombiTable1Ds;
  import Modelica.Blocks.Sources.CombiTimeTable;
  import Modelica.Blocks.Types.Smoothness.ConstantSegments;
  import SI=Modelica.SIunits;
  // Constants
  constant SI.Acceleration g[3] = {0,0,-10};
  // Wagon/Locomotive Parameters
  parameter SI.Mass m = 167000 "Total mass";
  parameter SI.Radius R = 0.5 "Traction wheel radius";
  parameter SI.Length len = 10 "Length of the wagon/locomotive";
  parameter SI.Efficiency eta_mec = 0.98 "Mechanical torque transmission
  efficiency";
  // Friction Parameters
  parameter Real A = 1.1224e-3;
  parameter Real B = 9.32e-6;
  parameter Real C = 3.044e-7;
  parameter Real epsf = 0.01;
  parameter SI.Conversions.NonSIunits.Velocity_kmh vsf = 3.0;
  parameter Real Af = 2.7;
  // Trajectory Data
  parameter SI.Length b = 1.0 "Track gauge";
  parameter String TableFile = "";
  parameter String rTable_main      = "r_main";
  parameter String drdsTable_main   = "drds_main";
  parameter String d2rds2Table_main = "d2rds2_main";
  parameter String rTable_branch      = "r_branch";
  parameter String drdsTable_branch   = "drds_branch";
  parameter String d2rds2Table_branch = "d2rds2_branch";
  parameter Boolean useBranch = false "Switch to alternate branch?";
  
  CombiTable1Ds RS_main(fileName = TableFile, tableName = rTable_main, columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
  CombiTable1Ds DRDS_main(fileName = TableFile, tableName = drdsTable_main, columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
  CombiTable1Ds D2RDS2_main(fileName = TableFile, tableName = d2rds2Table_main, columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
  
  CombiTable1Ds RS_branch(fileName = TableFile, tableName = rTable_branch, columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
  CombiTable1Ds DRDS_branch(fileName = TableFile, tableName = drdsTable_branch, columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
  CombiTable1Ds D2RDS2_branch(fileName = TableFile, tableName = d2rds2Table_branch, columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
  
  // CombiTimeTable RS(tableOnFile = true,
  //  fileName    = "Digital/r_table.csv",
  //  tableName   = "",           // dummy, not used for CSV
  //  columns     = {1, 2, 3, 4}, // col1 = s, col2–4 = x,y,z
  //  smoothness  = ConstantSegments);

  // CombiTimeTable DRDS(
  //  tableOnFile = true,
  //  fileName    = "Digital/drds_table.csv",
  //  tableName   = "",
  //  columns     = {1, 2, 3, 4}, // col1 = s, col2–4 = dr/ds
  //  smoothness  = ConstantSegments);
    
  //CombiTimeTable D2RDS2(
  //  tableOnFile = true,
  //  fileName    = "Digital/d2rds2_table.csv",
  //  tableName   = "",
  //  columns     = {1, 2, 3, 4}, // col1 = s, col2–4 = d²r/ds²
  //  smoothness  = ConstantSegments);
  // Inputs and Outputs
  TrainP3.WagonCoupling cf, ct;
  TrainP3.RotationalCoupling wheel;
  Interfaces.RealOutput s(start=0), s_wrap, v;
  
  // Variables
  SI.Position r[3];
  Real t[3], n[3];
  SI.Acceleration gt, gn, at, an;
  Real curvatura, k_Fatrito; // track curvature (1/m)
  //SI.Radius raio; // radius of curvature (m)
  SI.Force Fincl, Fatrito, Fcurva, Fmot, Fn;
  SI.Conversions.NonSIunits.Velocity_kmh v_kmh;
  
   // Read lines from the text file at translation time (must exist then)
  parameter String lengthsFile = "C:\\Users\\mchen\\Documents\\Repositories\\TrainModelSimulation\\Digital\\last_s.txt";
  parameter String lines[:] = Modelica.Utilities.Streams.readFile(lengthsFile);

  // number of lines read
  parameter Integer nlines = size(lines, 1);

  // Parse with scanReal; provide safe fallback values if file is missing/short
  parameter Modelica.SIunits.Length sEndMain   = if nlines >= 1 then Modelica.Utilities.Strings.scanReal(lines[1]) else 466.7705720361021;
  parameter Modelica.SIunits.Length sEndBranch = if nlines >= 2 then Modelica.Utilities.Strings.scanReal(lines[2]) else 467.93028857263903;
  
  parameter Modelica.SIunits.Length sEnd = sEndMain "Total track length";   // 63.46
  parameter SI.Length s0 = 0 "initial s position";

  discrete Modelica.SIunits.Length sEnd_local(start = if useBranch then sEndBranch else sEndMain);

  // Outputs to allow composition-level monitoring
  Interfaces.RealOutput r_out[3] "Cartesian position (x,y,z) of wagon center";

initial equation
  //s = s0;

equation

  //sEnd = if useBranch then sEndBranch else sEndMain;

// Trajectory data
  r = if useBranch then RS_branch.y else RS_main.y;
  t = normalize(if useBranch then DRDS_branch.y else DRDS_main.y);
  n = if useBranch then D2RDS2_branch.y else D2RDS2_main.y;
  
// Output
  r_out = r;
  
// Variables
  der(s) = v;
  
  // wrap s back into [0, sEnd)
  s_wrap = if s < sEnd_local then s else mod(s, sEnd_local);
  
  // initialize local sEnd already done by start above; handle runtime changes:
  when useBranch <> pre(useBranch) then
    // compute fraction along old track and remap to new length
    // pre(sEnd_local) is the old length
    if pre(sEnd_local) > 0 then
      s = s * (if useBranch then sEndBranch else sEndMain) / pre(sEnd_local);
    end if;
    // update local length to the newly selected one
    sEnd_local = if useBranch then sEndBranch else sEndMain;
  end when;
  
  at = der(v);
  v_kmh = SI.Conversions.to_kmh(v);
  curvatura = length(n);
  // allow straight segments (curvature = 0)
  //if curvatura > 0 then
    //raio * curvatura = 1;
    an   = v^2 * curvatura;
  //else
  // on straight, radius infinite, no normal accel
    // raio = Modelica.Constants.inf;
    //an   = 0;
  //end if;
  gt = g * t;
  gn = g * normalize(n);
// Slope forceF
  Fincl = m * gt;
// Friction force
  if abs(v_kmh) <= epsf then
    k_Fatrito = Af*v_kmh/epsf;
  elseif abs(v_kmh) > epsf and abs(v_kmh) <= vsf then
    k_Fatrito = Af*sign(v_kmh);
  else
    k_Fatrito = sign(v_kmh);
  end if;
  Fatrito = -k_Fatrito*(A+C*v_kmh^2+B*abs(v_kmh))*m*length(g);
 // Curvature force (zero on straight)
  //if curvatura > 1e-10 then
    Fcurva = -0.5 * b * curvatura * m * length(g);
  //else
  //  Fcurva = 0;
  //end if;
// Newton’s second law applied to mass moving along a path
  m * at = Fmot + Fincl + Fatrito + Fcurva + cf.F + ct.F;
  m * an = Fn + m * gn;
// Mechanical torque transmission
  wheel.tau = Fmot * R * eta_mec;
  der(wheel.phi) * R = v;
// External connections
  //connect(s, RS.u);
  //connect(s, DRDS.u);
  //connect(s, D2RDS2.u);
  
  // feed the tables with wrapped coordinate
  connect(s_wrap, RS_main.u);
  connect(s_wrap, RS_branch.u);
  connect(s_wrap, DRDS_main.u);
  connect(s_wrap, DRDS_branch.u);
  connect(s_wrap, D2RDS2_main.u);
  connect(s_wrap, D2RDS2_branch.u);
  
  cf.s = s + len/2;
  ct.s = s - len/2;
end WagonAlongPath;

  connector WagonCoupling
    import SI=Modelica.SIunits;
    SI.Position s "Distance along a path";
    flow SI.Force F "Applied longitudinal force";
  end WagonCoupling;

  connector RotationalCoupling
    "Wheel coupling, now compatible with any rotational flange"
    extends Modelica.Mechanics.Rotational.Interfaces.Flange;
  end RotationalCoupling;

  model Test_Composition
  // Railway track table
    TrainP3.GeneralInfo Track(file = "C:\\Users\\mchen\\Documents\\Repositories\\TrainModelSimulation\\Digital\\TurnoutTable.mat");
    
     // Read lines from the text file at translation time (must exist then)
    parameter String lengthsFile = "C:\\Users\\mchen\\Documents\\Repositories\\TrainModelSimulation\\Digital\\last_s.txt";
    parameter String lines[:] = Modelica.Utilities.Streams.readFile(lengthsFile);
  
    // number of lines read
    parameter Integer nlines = size(lines, 1);
  
    // Parse with scanReal; provide safe fallback values if file is missing/short
    parameter Modelica.SIunits.Length sEndMain   = if nlines >= 1 then Modelica.Utilities.Strings.scanReal(lines[1]) else 466.7705720361021;
    parameter Modelica.SIunits.Length sEndBranch = if nlines >= 2 then Modelica.Utilities.Strings.scanReal(lines[2]) else 467.93028857263903;
  
    // Choose which length to pass into the WagonAlongPath instance
    parameter Boolean startOnBranch = false;
    parameter Modelica.SIunits.Length sEnd = if startOnBranch then sEndBranch else sEndMain;
    //136 * 2 + 31 * Modelica.Constants.pi * 2 "Total track length";   // 63.46  10 + 50 * Modelica.Constants.pi / 2
    
    
    // Train Composition
    
    // Train 1
    TrainP3.WagonAlongPath locomotive(R = 0.96, TableFile = Track.file,
    b = 1, len = 1, s(start=50, fixed=true), sEnd=sEnd);
    TrainP3.WagonAlongPath wagon1(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    TrainP3.WagonAlongPath wagon2(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    TrainP3.WagonAlongPath wagon3(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    TrainP3.WagonAlongPath wagon4(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    
    // Train 2
    
    TrainP3.WagonAlongPath locomotive2(R = 0.96, TableFile = Track.file,
    b = 1, len = 1, sEnd=sEnd);
    
    // Traction system (train 1)
    Modelica.Blocks.Math.Feedback sum;
    Modelica.Blocks.Sources.Ramp ramp(duration = 100, height = 5); // duration = 240, height = 60 / 3.6
    Modelica.Blocks.Sources.Constant holdC(k = 5);
    Modelica.Blocks.Math.Min holdClamp;
    Modelica.Blocks.Continuous.PID PID(Td = 0, Ti = 2, k = 200000);
    Modelica.Mechanics.Rotational.Sources.Torque motor;
   
    // Traction system (train 2)
    Modelica.Blocks.Math.Feedback sum2;
    Modelica.Blocks.Sources.Ramp ramp2(duration = 100, height = 10); // duration = 240, height = 60 / 3.6
    Modelica.Blocks.Sources.Constant holdC2(k = 10);
    Modelica.Blocks.Math.Min holdClamp2;
    Modelica.Blocks.Continuous.PID PID2(Td = 0, Ti = 2, k = 200000);
    Modelica.Mechanics.Rotational.Sources.Torque motor2;
    
    // Collision Detector
    CollisionDetector cd(length1 = locomotive.len, length2 = locomotive2.len, safetyMargin = 0.5);
   
   equation
    //locomotive.sEnd = sEnd;
    
    // train 1
    connect(wagon2.cf, wagon1.ct); // connects first two wagons
    connect(wagon3.cf, wagon2.ct); // connects second pair of wagons
    connect(wagon4.cf, wagon3.ct); // connects third pair of wagons
    connect(locomotive.v, sum.u2); // feedback: y = u1 - u2
    connect(motor.flange, locomotive.wheel); // connects torque source to wheel?
    connect(PID.y, motor.tau); // inputs motor torque into PID?
    connect(locomotive.ct, wagon1.cf); // connects locomotive to first wagon
    connect(sum.y, PID.u); // result of feedback passed into PID?
    connect(ramp.y,   holdClamp.u1);
    connect(holdC.y,  holdClamp.u2);
    connect(sum.u1, holdClamp.y); // desired speed passed into feedback
    
    // train 2
    connect(locomotive2.v, sum2.u2); // feedback: y = u1 - u2
    connect(motor2.flange, locomotive2.wheel); // connects torque source to wheel?
    connect(PID2.y, motor2.tau); // inputs motor torque into PID?
    connect(sum2.y, PID2.u); // result of feedback passed into PID?
    connect(ramp2.y,   holdClamp2.u1);
    connect(holdC2.y,  holdClamp2.u2);
    connect(sum2.u1, holdClamp2.y); // desired speed passed into feedback
    
    // collision detection
    connect(locomotive.r_out, cd.p1);
    connect(locomotive2.r_out, cd.p2);
    
    //When s reaches or exceeds sEnd, terminate simulation
    //when locomotive.s >= sEnd then
    //Modelica.Utilities.Streams.print(
    //    "Reached end of track at s=" + String(locomotive.s) + "m");
    //  terminate("End of track reached");
    //end when;
  end Test_Composition;

  record GeneralInfo
    extends Modelica.Icons.Record;
    parameter String file = "";
  end GeneralInfo;

  model CollisionDetector
    import SI = Modelica.SIunits;
    input Modelica.Blocks.Interfaces.RealInput p1[3] "position of vehicle 1 (x,y,z)";
    input Modelica.Blocks.Interfaces.RealInput p2[3] "position of vehicle 2 (x,y,z)";
    parameter SI.Length length1 = 1 "length of vehicle 1 (m)";
    parameter SI.Length length2 = 1 "length of vehicle 2 (m)";
    parameter SI.Length safetyMargin = 0.5 "extra clearance (m)";
  protected
    Real dist "Euclidean distance between centers";
    discrete Boolean collided(start=false) "true after first collision event";
  equation
    dist = sqrt( (p1[1]-p2[1])^2 + (p1[2]-p2[2])^2 + (p1[3]-p2[3])^2 );
  
    when not pre(collided) and dist <= (length1/2 + length2/2 + safetyMargin) then
      collided = true;
      // print and then stop simulation with a clear message
      Modelica.Utilities.Streams.print("Collision detected at time=" + String(time) 
        + " distance=" + String(dist));
      assert(false, "Collision detected between vehicles (distance <= threshold).");
    end when; 
  end CollisionDetector;
end TrainP3;
