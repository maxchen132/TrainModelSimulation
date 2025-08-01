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
      CombiTable1Ds RS(fileName = TableFile, tableName = "r", columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
      CombiTable1Ds DRDS(fileName = TableFile, tableName = "drds", columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
      CombiTable1Ds D2RDS2(fileName = TableFile, tableName = "d2rds2", columns = {2,3,4}, tableOnFile = true, smoothness = ConstantSegments);
      // Inputs and Outputs
      TrainP3.WagonCoupling cf, ct;
      TrainP3.RotationalCoupling wheel;
      Interfaces.RealOutput s(start=0), s_wrap, v;
      // Variables
      SI.Position r[3];
      Real t[3], n[3];
      SI.Acceleration gt, gn, at, an;
      Real curvatura, k_Fatrito; // track curvature (1/m)
      // SI.Radius raio; // radius of curvature (m)
      SI.Force Fincl, Fatrito, Fcurva, Fmot, Fn;
      SI.Conversions.NonSIunits.Velocity_kmh v_kmh;
      
      parameter Modelica.SIunits.Length sEnd = 20 + Modelica.Constants.pi * 2 * 2 "Total track length";   // 63.46
    equation
  // Trajectory data
      r = RS.y;
      t = normalize(DRDS.y);
      n = D2RDS2.y;
  // Variables
      der(s) = v;
      
      // wrap s back into [0, sEnd)
      s_wrap = if s < sEnd then s else mod(s, sEnd);
      
      at = der(v);
      v_kmh = SI.Conversions.to_kmh(v);
      curvatura = length(n);
      // allow straight segments (curvature = 0)
      //if curvatura > 0 then
        // raio = 1/curvatura;
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
      connect(s, RS.u);
      connect(s, DRDS.u);
      connect(s, D2RDS2.u);
      
      // feed the tables with wrapped coordinate
      //connect(s_wrap, RS.u);
      //connect(s_wrap, DRDS.u);
      //connect(s_wrap, D2RDS2.u);
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
    TrainP3.GeneralInfo Track(file = "C:\\Users\\mchen\\Documents\\Repositories\\TrainModelSimulation\\Digital\\TrackTable.mat");
    parameter Modelica.SIunits.Length sEnd = 136 * 2 + Modelica.Constants.pi * 2 * 31 "Total track length";   // 63.46
    // Train Composition
    
    TrainP3.WagonAlongPath locomotive(R = 0.96, TableFile = Track.file,
    b = 1, len = 1);
    //TrainP3.WagonAlongPath wagon1(A = 8.253e-4, B = 1.405e-5, C =
    //3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    //TrainP3.WagonAlongPath wagon2(A = 8.253e-4, B = 1.405e-5, C =
    //3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    //TrainP3.WagonAlongPath wagon3(A = 8.253e-4, B = 1.405e-5, C =
    //3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    //TrainP3.WagonAlongPath wagon4(A = 8.253e-4, B = 1.405e-5, C =
    //3.5116e-8, TableFile = Track.file, b = 1, m = 300000);
    // Traction system
    Modelica.Blocks.Math.Feedback sum;
    Modelica.Blocks.Sources.Ramp ramp(duration = 2, height = 180 / 3.6); // duration = 240, height = 60 / 3.6
    Modelica.Blocks.Continuous.PID PID(Td = 0, Ti = 2, k = 200000);
    Modelica.Mechanics.Rotational.Sources.Torque motor;
   equation
    //locomotive.sEnd = sEnd;
    //connect(wagon2.cf, wagon1.ct); // connects first two wagons
    //connect(wagon3.cf, wagon2.ct); // connects second pair of wagons
    //connect(wagon4.cf, wagon3.ct); // connects third pair of wagons
    connect(locomotive.v, sum.u2); // feedback: y = u1 - u2
    connect(motor.flange, locomotive.wheel); // connects torque source to wheel?
    connect(PID.y, motor.tau); // inputs motor torque into PID?
    //connect(locomotive.ct, wagon1.cf); // connects locomotive to first wagon
    connect(sum.y, PID.u); // result of feedback passed into PID?
    connect(sum.u1, ramp.y); // desired speed passed into feedback
    
    // 2) When s reaches or exceeds sEnd, terminate simulation
    when locomotive.s >= sEnd then
      Modelica.Utilities.Streams.print(
        "Reached end of track at s=" + String(locomotive.s) + "m");
      terminate("End of track reached");
    end when;
  end Test_Composition;

  record GeneralInfo
    extends Modelica.Icons.Record;
    parameter String file = "";
  end GeneralInfo;
end TrainP3;
