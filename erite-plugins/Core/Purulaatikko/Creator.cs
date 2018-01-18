using System;
using Tekla.Structures.Model;
using Tekla.Structures.Geometry3d;
using System.Linq;
using System.Windows.Forms;
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
                    switch (partSpec.section)
                    {
                        case "footing":
                        {
                            GenerateConcreteBeams(partSpec.data, ref partCounter);
                            break;
                        }
                        case "sockle":
                        {
                            //GenerateConcretedStuff(partSpec.data, ref partCounter);
                            break;
                        }
                        default:
                        {
                            //GenerateWoodenBeams(partSpec.data, ref partCounter);
                            // default is wood
                            break;
                        }
                    }
                }
            }
            if ( 0 == partCounter )
            {
                System.Diagnostics.Debug.WriteLine($"[ERITE] failed to do nothin goddamit.");
            }
        }

        private void GenerateConcreteBeams(JsPart[] data, ref int partCounter)
        {
            //var internalCounter .. uh todo label etc.
            foreach(var beamSpec in data)
            {
                var beam = new Beam
                {
                    StartPoint = beamSpec.points[0].ToTS(),
                    EndPoint = beamSpec.points[1].ToTS(),
                    Material = ChainSaw.FromString(beamSpec.material),
                    Profile = new Profile{
                        ProfileString = beamSpec.profile
                    }
                };
                beam.Insert();
                    //(, );
            }
        }

        private void GenerateConcretedStuff(JsPart[] data, ref int partCounter)
        {
            throw new NotImplementedException();
        }

        private void GenerateWoodenBeams(JsPart[] data, ref int counter)
        {
            throw new NotImplementedException();
        }

        protected void SetToolWorkplane()
        {

        }

    }
}
