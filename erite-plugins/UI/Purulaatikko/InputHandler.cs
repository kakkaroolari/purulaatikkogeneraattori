using System.Collections.Generic;
using Tekla.Structures;
using Tekla.Structures.Geometry3d;
using Tekla.Structures.Plugins;
using EritePlugins.Core.Purulaatikko;
using System;
using Tekla.Structures.Model;

namespace EritePlugins.UI.Purulaatikko
{
    internal class InputHandler
    {
        private readonly StructuresData _data;
        private PurulaatikkoAttributes _attributes;
        private bool _isInputValid;

        internal InputHandler(StructuresData data)
        {
            _data = data;
        }

        internal PurulaatikkoAttributes Attributes
        {
            get { return _attributes; }
        }

        internal StructuresData Data
        {
            get { return _data; }
        }

        internal bool IsInputValid
        {
            get { return _isInputValid; }
        }

        internal void SetAttributes()
        {
            _attributes = new PurulaatikkoAttributes()
            {
                PartsAttributeFile = _data.PartsAttributeFile
            };
        }

        internal void SetInputObjects(List<PluginBase.InputDefinition> input)
        {
            //if (input.Count != 1)
            //{
            //    throw new ApplicationException("No point");
            //}

            var columnId = input[0].GetInput() as Identifier;

            //var skeletor = new Tekla.Structures.Model.ModelObjectSelector();
            // skeletor.SelectModelObject(columnId) as Beam;


            _isInputValid = true;
        }

    }

}
