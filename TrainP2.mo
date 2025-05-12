package TrainP2
  model TrainAlongPath
    import Modelica.Math.Vectors.length;
    import Modelica.Math.Vectors.normalize;
    import Modelica.Blocks.Interfaces;
    import Modelica.Blocks.Tables.CombiTable1Ds;
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
    
    // Fricion Parameters
    parameter Real A = 1.1224e-3;
    parameter Real B = 9.32e-6;
    parameter Real C = 3.044e-7;
    parameter Real epsf = 0.01;
    parameter SI.Conversions.NonSIunits.Velocity_kmh vsf = 3.0;
    parameter Real Af = 2.7;
    
    // Trajectory Data
    parameter SI.Length b = 1.0 "Track gauge";
    parameter String TableFile = "";
    CombiTable1Ds RS(fileName = TableFile, tableName = "r", columns = {2,3,4},
    tableOnFile = true, smoothness = ConstantSegments);
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
  end TrainAlongPath;
end TrainP2;
