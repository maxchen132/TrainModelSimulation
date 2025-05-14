package TrainP3
  model WagonAlongPath
    import Modelica.Math.Vectors.length;
    import Modelica.Math.Vectors.normalize;
    import Modelica.Blocks.Interfaces;
    import Modelica.Blocks.Tables.CombiTable1Ds;
    import Modelica.Blocks.Types.Smoothness.ConstantSegments;
    import SI=Modelica.SIunits;
    
    // Constants
    constant SI.Acceleration g[3] = {0,0,-10};
    
    // Wagon/Locomotive Parameters
    parameter SI.Mass m = 800 "Total mass";
    parameter SI.Radius R = 0.005 "Traction wheel radius";
    parameter SI.Length len = 0.1 "Length of the wagon/locomotive";
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
    parameter String TableFile = "/Users/nathanyao/files/cs/Open-Modelica/TrainModelSimulation/TrackTable.mat";
    CombiTable1Ds RS(fileName = TableFile, tableName = "r", columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
    CombiTable1Ds DRDS(fileName = TableFile, tableName = "drds", columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
    CombiTable1Ds D2RDS2(fileName = TableFile, tableName = "d2rds2", columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
    
    // Inputs and Outputs
    Locomotives.Coupling cf, ct;
    Locomotives.RotationalCoupling wheel;
    Interfaces.RealOutput s(start=0), v;
    
    // Variables
    SI.Position r[3];
    Real t[3], n[3];
    SI.Acceleration gt, gn, at, an;
    Real curvatura(min=1e-10), k_Fatrito;
    SI.Radius raio(min=1e-10);
    SI.Force Fincl, Fatrito, Fcurva, Fmot, Fn;
    SI.Conversions.NonSIunits.Velocity_kmh v_kmh;
    
  equation
    // Trajectory data
    r = RS.y;
    t = normalize(DRDS.y);
    n = D2RDS2.y;
    
    // Variables
    der(s) = v;
    at = der(v);
    v_kmh = SI.Conversions.to_kmh(v);
    curvatura = length(n);
    curvatura*raio = 1;
    an = v ^ 2 * curvatura;
    gt = g * t;
    gn = g * normalize(n);
    
    // Slope force
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
    
    // Curvature force
    Fcurva = -(0.5*b*curvatura)*m*length(g);
    
    // Newton’s second law applied to mass moving along a path
    m * at = Fmot + Fincl + Fatrito + Fcurva + cf.F + ct.F;
    m * an = Fn + m * gn;
    
    // Mechanical torque transmission
    wheel.T = Fmot * R * eta_mec;
    der(wheel.phi) * R = v;
    
    // External connections
    connect(s, Rs.u);
    connect(s, DRDS.u);
    connect(s, D2RDS2.u);
    cf.s = s + len/2;
    ct.s = s - len/2;
  end WagonAlongPath;

  connector WagonCoupling
    import SI=Modelica.SIunits;
    SI.Position s "Distance along a path";
    flow SI.Force F "Applied longitudinal force";
  end WagonCoupling;

  connector RotationalCoupling
    import SI=Modelica.SIunits;
    SI.Angle phi "Angular position";
    flow SI.Torque T "Applied torque";
  end RotationalCoupling;

  model Test_Composition
  // Railway track table
    Locomotives.GeneralInfo Track(file = "/Users/nathanyao/files/cs/Open-Modelica/TrainModelSimulation/TrackTable.mat");
    // Train Composition
    Locomotives.ConnectMassAlongPath locomotive(R = 0.96, TableFile = Track.file,
    b = 1, len = 13.8);
    Locomotives.ConnectMassAlongPath wagon1(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    Locomotives.ConnectMassAlongPath wagon2(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    Locomotives.ConnectMassAlongPath wagon3(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    Locomotives.ConnectMassAlongPath wagon4(A = 8.253e-4, B = 1.405e-5, C =
    3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    // Traction system
    Modelica.Blocks.Math.Feedback sum;
    Modelica.Blocks.Sources.Ramp ramp(duration = 240, height = 60 / 3.6);
    Modelica.Blocks.Continuous.PID PID(Td = 0, Ti = 2, k = 200000);
    Modelica.Mechanics.Rotational.Sources.Torque motor;
   equation
    connect(wagon2.cf, wagon1.ct);
    connect(wagon3.cf, wagon2.ct);
    connect(wagon4.cf, wagon3.ct);
    connect(locomotive.v, sum.u2);
    connect(motor.flange, locomotive.wheel);
    connect(PID.y, motor.tau);
    connect(locomotive.ct, wagon1.cf);
    connect(sum.y, PID.u);
    connect(sum.u1, ramp.y);
  end Test_Composition;
end TrainP3;