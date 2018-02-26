using System;
using System.Collections;
using System.Collections.Generic;
using Tekla.Structures.Model;
using Tekla.Structures.Geometry3d;
using System.Linq;
using System.Windows.Forms;
using EritePlugins.Common;
using SwecoToolbar;
using Tekla.Structures.Model.UI;
//using ChainSaw;


namespace EritePlugins.Core.Purulaatikko
{
    public class Creator
    {
        private PurulaatikkoAttributes _attributes;
        private Model _model;

        public void SetAttributes(PurulaatikkoAttributes attributes)
        {
            _attributes = attributes;
        }

        public bool Create()
        {
            //var original = Tekla.GetCurrentTransformationPlane();
            try
            {
                System.Diagnostics.Debug.WriteLine("[ERITE] Core business..");
                SetToolWorkplane();

                DoParts();
            }
            catch (Exception e)
            {
                Tracer._trace($"[ERITE] Catastrophic failure: {e.Message}\n{e.StackTrace}");
            }
            finally
            {
                //Tekla.SetCurrentTransformationPlane(original);
            }
            return true;
        }

        private void DoParts()
        {
            var list = JsonReader.ReadItIn(_attributes.PartsAttributeFile);
            System.Diagnostics.Debug.WriteLine($"[ERITE] Found {list?.Count} part specs to do.");

            _model = new Model();
            var partCounter = 0;
            if (null != list)
            {
                foreach (JsSection partSpec in list)
                {
                    if (null == partSpec) continue;
                    using (var csys = TemporaryWorkplane.FromJsPlane(partSpec.coordinate_system))
                    {
                        int warn = partCounter;
                        ForNowCreateAllBeams(partSpec, ref partCounter);
                        if (warn == partCounter)
                        {
                            System.Diagnostics.Debug.WriteLine($"[ERITE] No elements in section {partSpec.section}");
                        }
                    }
                    //switch (partSpec.section)
                    //{
                    //    case "footing":
                    //    {
                    //        GenerateConcreteBeams(partSpec.data, ref partCounter);
                    //        break;
                    //    }
                    //    case "sockle":
                    //    {
                    //        //GenerateConcretedStuff(partSpec.data, ref partCounter);
                    //        break;
                    //    }
                    //    default:
                    //    {
                    //        GenerateWoodenBeams(partSpec.data, ref partCounter);
                    //        // default is wood
                    //        break;
                    //    }
                    //}
                }
            }
            if ( 0 == partCounter )
            {
                System.Diagnostics.Debug.WriteLine($"[ERITE] failed to do nothin goddamit.");
            }
        }

        //private void GenerateConcreteBeams(JsPart[] data, ref int partCounter)
        //{
        //    ForNowCreateAllBeams(data, ref partCounter, "Footing");
        //}

        //private void GenerateConcretedStuff(JsPart[] data, ref int partCounter)
        //{
        //    ForNowCreateAllBeams(data, ref partCounter, "Footing");
        //}

        //private void GenerateWoodenBeams(JsPart[] data, ref int counter)
        //{
        //    ForNowCreateAllBeams(data, ref counter, "Stud");
        //}

        private void ForNowCreateAllBeams(JsSection section, ref int counter)
        {
            JsPart[] data = section.parts;
            string labelPrefix = section.section;
            Assembly assembly = null;
            int labelCounter = 0;
            List<Tuple<AABB, Part>> cutSolids = CreateSolids(section.cutobjects);
            List<Tuple<Tuple<Point, Point, Point>, Plane>> cutPlanes = CreatePlanes(section.planes);
            Tracer._trace($"Found {cutSolids.Count} AABB's to cut with");

            string label = $"{labelPrefix}_{++labelCounter}";
            foreach (var beamSpec in data)
            {
                try
                {
                    var beam = CreateBeamOrPoly(beamSpec);
                    if (beam.Insert())
                    {
                        counter++;
                        if (null == assembly)
                        {
                            assembly = beam.GetAssembly();
                        }
                        else
                        {
                            assembly.Add(beam);
                            assembly.Modify();
                        }

                        beam.SetLabel(label);
                        TryApplyCuts(beam, cutSolids);
                        TryApplyCuts(beam, cutPlanes);
                    }
                }
                catch (Exception e)
                {
                    Tracer._trace($"Part failure: {label}");
                    throw;
                }
            }
            // "finally"
            foreach (var cutItem in cutSolids)
            {
                cutItem.Item2.Delete();
            }
        }

        private List<Tuple<Tuple<Point, Point, Point>, Plane>> CreatePlanes(JsPlane[] planeDefs)
        {
            var planes = new List<Tuple<Tuple<Point, Point, Point>, Plane>>();
            if (null == planeDefs) return planes;

            foreach (var planeDef in planeDefs)
            {
                var origin = planeDef.point1.GetPoint();
                var axisX = new Vector(planeDef.point3.GetPoint() - planeDef.point1.GetPoint());
                var axisY = new Vector(planeDef.point2.GetPoint() - planeDef.point1.GetPoint());
                var plane = new Plane
                {
                    Origin = origin,
                    AxisX = axisX,
                    AxisY = axisY
                };
                /*
                var normal = axisX.Cross(axisY);
                var geomPlane = new GeometricPlane(origin, normal);
                */
                var p1 = planeDef.point1.GetPoint();
                var p2 = planeDef.point2.GetPoint();
                var p3 = planeDef.point3.GetPoint();
                var points = Tuple.Create(p1, p2, p3);
                planes.Add(Tuple.Create(points, plane));
            }

            return planes;
        }

        private List<Tuple<AABB, Part>> CreateSolids(JsCutobject[] sectionCutobjectsDefs)
        {
            var aabbs = new List<Tuple<AABB, Part>>();
            if (null == sectionCutobjectsDefs) return aabbs;

            foreach (var pointPair in sectionCutobjectsDefs)
            {
                //if (2 == pointPair.Length)
                //{
                    var lowleft = pointPair.min_point.GetPoint();
                var highright = pointPair.max_point.GetPoint();
                var pointList = new List<Point> { lowleft, highright };
                var midy = pointList.Average(p => p.Y);
                //var midy = (highright.Y - lowleft.Y) / 2;
                    //var midZ = pointPair.Select(p => p.GetPoint()).Average(p => p.Z);
                    var maxx = highright.X;
                    var minx = lowleft.X;
                    var maxZ = highright.Z;
                    var minZ = lowleft.Z;
                    int height = Convert.ToInt32(maxZ - minZ);
                    int width = Convert.ToInt32(highright.Y - lowleft.Y);
                    var profileString = $"{width}*{height}";
                    var startPoint = new Point(minx, midy, 0);
                    var endPoint = new Point(maxx, midy, 0);
                    Tracer._trace($"Boolean solid: {startPoint} -> {endPoint}, wid: {width}, hei: {height}.");
                    var operativePart = new Beam
                    {
                        StartPoint = startPoint,
                        EndPoint = endPoint,
                        Position = new Position
                        {
                            Depth = Position.DepthEnum.MIDDLE,
                            Plane = Position.PlaneEnum.MIDDLE,
                            Rotation = Position.RotationEnum.FRONT
                        },
                        Profile = new Profile
                        {
                            ProfileString = profileString
                        },
                        Class = BooleanPart.BooleanOperativeClassName
                    };
                    operativePart.Insert();
                    var aabb = new AABB(lowleft, highright);
                    aabbs.Add(Tuple.Create<AABB, Part>(aabb, operativePart));
                //}
                //else
                //{
                //    Tracer._trace("Strange cut solid, unable to comply.");
                //}
            }

            return aabbs;
        }

        private void TryApplyCuts(Part part, List<Tuple<AABB, Part>> cutSolids)
        {
            if ( null == cutSolids ) return;

            var partBox = part.GetAABB();
            // check collision
            foreach (var cutObjects in cutSolids)
            {
                var aabb = cutObjects.Item1;
                var operativePart = cutObjects.Item2;
                if (!GeometryUtils.testAABBAABB(aabb, partBox)) continue;

                BooleanPart Beam = new BooleanPart();
                Beam.Father = part;
                Beam.SetOperativePart(operativePart);
                if (!Beam.Insert())
                {
                    Tracer._trace("Insert failed!");
                }
                Tracer._trace($"Cut solid: {part.Name}.");
            }

        }

        private void TryApplyCuts(Part part, List<Tuple<Tuple<Point, Point, Point>, Plane>> cutPlanes)
        {
            if (null == cutPlanes) return;

            var partBox = part.GetSolid();
            // check collision
            foreach (var cutPlaneDef in cutPlanes)
            {
                var operativePart = cutPlaneDef.Item2;
                var pps = cutPlaneDef.Item1;
                var intersection = partBox.IntersectAllFaces(pps.Item1, pps.Item2, pps.Item3);
                if (intersection.IsNullOrEmpty()) continue;

                var cutPlane = new CutPlane();
                cutPlane.Father = part;
                cutPlane.Plane = operativePart;
                if (!cutPlane.Insert())
                {
                    Tracer._trace("Insert failed!");
                }
                Tracer._trace($"Cut solid: {part.Name}.");
            }

        }

        private Part CreateBeamOrPoly(JsPart beamSpec)
        {
            Part beam = null;
            if (null == beamSpec || null == beamSpec.points || beamSpec.points.Length < 2) return null;
            Position.PlaneEnum plane = Position.PlaneEnum.MIDDLE; //< woods
            if (beamSpec.points.Length == 2)
            {
                beam = new Beam
                {
                    StartPoint = beamSpec.points[0].ToTS(),
                    EndPoint = beamSpec.points[1].ToTS(),
                    Position = new Position()
                    {
                        Depth = Position.DepthEnum.MIDDLE,
                        Plane = Position.PlaneEnum.MIDDLE
                    }
                };
                if (null != beamSpec.rotation)
                {
                    beam.Position.Rotation = EnumConverter.TryFromInt((int)beamSpec.rotation, Position.RotationEnum.FRONT);
                }
            }
            else
            {
                beam = new PolyBeam
                {
                    Contour = new Contour()
                    {
                        ContourPoints = new ArrayList(beamSpec.points.Select(p => new ContourPoint(p.ToTS(), null)).ToList())
                    },
                    Position = new Position()
                    {
                        Depth = Position.DepthEnum.FRONT,
                        Plane = Position.PlaneEnum.LEFT
                    },
                    
                };
            }

            beam.Material = ChainSaw.FromString(beamSpec.material);
            beam.Profile = new Profile
            {
                ProfileString = beamSpec.profile
            };
            if (null != beamSpec?.klass)
            {
                beam.Class = beamSpec.klass.ToString();
            }
            //beam.Position = new Position
            //{
            //    Depth = Position.DepthEnum.,
            //    Plane = plane
            //};
            return beam;
        }

        protected void SetToolWorkplane()
        {

        }

    }
}
