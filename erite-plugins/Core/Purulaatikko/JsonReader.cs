using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace EritePlugins.Core.Purulaatikko
{
    public class JsonReader
    {
        // read python parts in i.e. python-proto\data.json

        public static IList<JsPart> ReadItIn(string FileLoc)
        {
            List<JsPart> parts = null;
            try
            {
                //var ro = new JsRootobject();
                StreamReader sr = new StreamReader(FileLoc);
                string jsonString = sr.ReadToEnd();
                JavaScriptSerializer ser = new JavaScriptSerializer();
                var ro = ser.Deserialize<List<JsPart>>(jsonString);
                parts = ro/*.Property1*/.ToList();
            }
            catch (Exception e)
            {
                System.Diagnostics.Debug.WriteLine($"[ERITE] Json error: {e.Message}");
            }
            return parts;
        }
    }


    public class JsRootobject
    {
        public JsPart[] Property1 { get; set; }
    }

    public class JsPart
    {
        public string profile { get; set; }
        public JsPoint[] points { get; set; }
        public string material { get; set; }
    }

    public class JsPoint
    {
        public double x { get; set; }
        public double y { get; set; }
        public double z { get; set; }
    }


}
