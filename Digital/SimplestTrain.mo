model SimplestTrain
  import Modelica;
  import Modelica.Blocks;
  import Modelica.Blocks.Sources;
  import Modelica.Blocks.Continuous;
  import Modelica.Mechanics.MultiBody;
  import Modelica.Mechanics.Translational;
  
  // Parameters (currently placeholder values)
  parameter Real m = 1;    
  parameter Real F = 1;    
  parameter Real b = 0.5;        
  parameter Real R = 0.5;    
  parameter Real L = 1;
  parameter Real startV = 5;

  // Motion variables
  Real x(start=0);
  Real v(start=startV);
  Real a;
  Real F_friction;

  /*
  parameter Real startValue = startV / R;

  // MultiBody components
  
  MultiBody.Parts.BodyShape trainBody( 
    r={0,0,0}, 
    m=m, 
    shapeType="box", 
    length=0.1, width=0.05, height=0.05
  );
  
  MultiBody.Joints.Revolute leftCurve(
    n={0,0,1}, 
    phi(start=0, fixed=true), 
    w(start=startValue)
  );

  MultiBody.Joints.Revolute rightCurve( 
    n={0,0,1},  
    phi(start=0, fixed=true), 
    w(start=startValue)
  );
  
  Blocks.Sources.Constant speedRef(k=10);
  Blocks.Continuous.PI speedController(k=100, T=0.1);

  MultiBody.Parts.FixedTranslation straight1(r={L, 0, 0});
  MultiBody.Parts.FixedTranslation straight2(r={-L, 0, 0});
  
  Translational.Sources.Force trainForce;
  Translational.Components.Mass trainMass(m=m);
  */

equation
  // Friction force
  F_friction = b * v;
  a = (F - F_friction) / m;

  // Kinematics
  der(x) = v;
  der(v) = a;

  /*
  // Track connections
  connect(straight1.frame_b, leftCurve.frame_a);
  connect(leftCurve.frame_b, straight2.frame_a);
  connect(straight2.frame_b, rightCurve.frame_a);
  connect(rightCurve.frame_b, straight1.frame_a);

  // Train movement
  connect(trainBody.frame_a, straight1.frame_b);
  connect(trainForce.flange, trainMass.flange_a);

  // Speed control
  connect(speedRef.y, speedController.u);
  connect(speedController.y, trainForce.f);
  */

  annotation (experiment(StopTime=20), Diagram);
end SimplestTrain;
