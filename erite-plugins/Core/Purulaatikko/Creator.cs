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
            System.Diagnostics.Debug.WriteLine($"[ERITE] Found {list.Count} part specs to do.");
        }

        protected void SetToolWorkplane()
        {

        }

    }
}
