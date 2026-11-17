import { createSlice } from "@reduxjs/toolkit";

const initialState={
    items:[],
    totalTask:0
}

const taskSlice= createSlice({
    name:'tasks',
    initialState,
    reducers:{
        addTask:(state,action)=>{
            state.items.push(action.payload);
            state.totalTask=state.items.length;
        },
        deleteTask:(state,action)=>{
            state.items= state.items.filter(
                task=>task.id!== action.payload
            );
            state.totalTask=state.items.length; 
        },
        toggleTask:(state,action)=>{
            const task = state.items.find(
                (task)=>task.id===action.payload
            );

            if(task) task.isCompleted=!task.isCompleted;
        }
    }
})

export const {addTask,deleteTask,toggleTask} = taskSlice.actions;
export default taskSlice.reducer;