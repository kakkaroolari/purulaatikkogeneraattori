using System;
using System.Collections;
using Tekla.Structures.Model;
using Tekla.Structures.Geometry3d;
using System.Linq;
using System.Windows.Forms;
using EritePlugins.Common;
using Tekla.Structures.Model.UI;


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
                System.Diagnostics.Debug.WriteLine($"[ERITE] Catastrophic failure: {e.Message}");
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
                        ForNowCreateAllBeams(partSpec.parts, ref partCounter, partSpec.section);
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

        private void ForNowCreateAllBeams(JsPart[] data, ref int counter, string labelPrefix)
        {
            Assembly assembly = null;
            int labelCounter = 0;
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
                    }
                }
                catch (Exception e)
                {
                    System.Diagnostics.Debug.WriteLine($"[ERITE] Part failure: {label}");
                    throw;
                }
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
