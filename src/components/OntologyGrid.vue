<template>
  <!-- <ag-grid-vue
   class="ag-theme-alpine"
   style="height: 500px"
   :columnDefs="columnDefs.value"
   :rowData="rowData.value"
   :defaultColDef="defaultColDef"
   rowSelection="multiple"
   animateRows="true"
   @cell-clicked="cellWasClicked"
   @grid-ready="onGridReady"
 >
 </ag-grid-vue> -->
 <div id="controller-bar" class="flex flex-row justify-between w-full">
    <div class="flex flex-row space-x-2 m-2 w-2/3">
        <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-1 rounded" @click="expandRows()">
            Expand All
        </button>
        <button class="bg-slate-500 hover:bg-blue-700 text-white font-bold py-1 px-1 rounded" @click="collapseRows()">
            Collapse All
        </button>
        <div class="border rounded w-2/3">
            <input class="w-full" type="search" id="filter-text-box" placeholder="Filter..." v-on:input="onFilterTextBoxChanged()">
        </div>
    </div>
    <div class="flex flex-row m-2">
        <div id="version">
            v1.3.2
        </div>
    </div>
    
</div>
<ag-grid-vue
    class="ag-theme-alpine h-full"
    :treeData="true"
    :getDataPath="getDataPath"
    :columnDefs="columnDefs.value"
    :rowData="data"
    :defaultColDef="defaultColDef"
    :autoGroupColumnDef="autoGroupColumnDef"
    rowSelection="multiple"
    animateRows="true"
    @cell-clicked="cellWasClicked"
    @grid-ready="onGridReady"
    >
</ag-grid-vue>
</template>

<script>
import { AgGridVue } from "ag-grid-vue3";  // the AG Grid Vue Component
import 'ag-grid-community/styles/ag-grid.css'; // Core grid CSS, always needed
import 'ag-grid-community/styles/ag-theme-alpine.css'; // Optional theme CSS

import { reactive, onMounted, ref } from "vue";

import data from "../assets/data.json"

export default {
components: {
   AgGridVue,
 },
setup() {
    const gridApi = ref(null); // Optional - for accessing Grid's API

    // Obtain API from grid's onGridReady event
    const onGridReady = (params) => {
        console.log("Grid Ready...")
        gridApi.value = params.api;
    };

    const rowData = reactive({}); // Set rowData to Array of Objects, one Object per Row

    // Each Column Definition results in one Column.
    const columnDefs = reactive({
        value: [
            { field: "desc"},
            { field: "uri", hide: true },
            { field: "namespace" },
            { field: "prefix" },
            // { field: "term" }
        ],
    });

    // DefaultColDef sets props common to all Columns
    const defaultColDef = {
        sortable: true,
        // filter: 'agTextColumnFilter',
        flex: 1,
        resizable: true
    };

    const getDataPath = (data) => {
            // const raw = data.path.agGridPath;
            const raw = data.path.full; // this should help with duplicates. Will then use a formatter function to display term only.

            
            return raw
    }

    const classValueGetter = (params) => {
        // SET ICON
        let icon = "❔" //🧱 🟢 ❔
        try {
            if(params.data.prefix == "brick") {
                icon = "🧱"
            } else if (params.data.prefix == "switch") {
                icon = "🟢"
            } else if (params.data.prefix == "owl") {
                icon = "🦉"
            }
            
        } catch {
            console.log(`Grid::Class: No icon for given namespace of: ${params.value}`)
        }
        // SET NAME (TERM)
        try {
            return `${params.data.term} &nbsp; ${icon}`
        } catch {
            console.log(`Grid::Class: No term available for: ${params.value}`)
            return `${params.value} &nbsp; ${icon}`
        }
    }
    // Example load data from sever
    // onMounted(() => {
    //     fetch("https://www.ag-grid.com/example-assets/row-data.json")
    //     .then((result) => result.json())
    //     .then((remoteRowData) => (rowData.value = remoteRowData));
    // });

    function onFilterTextBoxChanged() {
      gridApi.value.setQuickFilter(
        document.getElementById('filter-text-box').value
      );
      gridApi.value.expandAll();
    }

    function collapseRows() {
        gridApi.value.collapseAll();
    }

    function expandRows() {
        gridApi.value.expandAll();
    }

    return {
        onGridReady,
        columnDefs,
        rowData,
        defaultColDef,
        cellWasClicked: (event) => { // Example of consuming Grid Event
            console.log("cell was clicked", event);
        },
        deselectRows: () =>{
            gridApi.value.deselectAll()
        },
        getDataPath,
        data,
        autoGroupColumnDef: {
                headerName: "Class",
                width: 300,
                sortable: true,
                cellRendererParams: {
                    suppressCount: true,
                    innerRenderer: classValueGetter
                },
                filter: 'agTextColumnFilter',
                resizable: true
        },
        onFilterTextBoxChanged,
        collapseRows,
        expandRows
    };
}
};
</script>