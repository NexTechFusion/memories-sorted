function app(){return{
    tab:'home',loading:false,
    expIns:null,mergeSource:null,mergePending:false,
    searchQ:'',searchRes:null,
    moments:[],people:[],allPhotos:[],topPhotos:[],insights:[],
    pgOpen:false,pgPerson:null,pgPhotos:[],
    mgOpen:false,mgMoment:null,mgPhotos:[],mgEdit:false,
    tlOpen:false,tlPerson:null,tlPhotos:[],
    lbOpen:false,lbIdx:0,lbPhotos:[],lbDetail:true,lbST:0,lbMenuOpen:false,lbCaptionEdit:false,lbCaption:'',lbMoveShow:false,lbDeleteShow:false,
    // Zoom state (pinch, double-tap, scroll wheel)
    lbZ:{s:1,x:0,y:0,min:1,max:5,panning:false,startX:0,startY:0,pinchDist:0,pinchScale:1,lastTap:0},
    rnOpen:false,rnId:null,rnInput:'',
    addMomentOpen:false,newMomentLabel:'',
    momentEdit:{show:false,action:'Rename',input:'',target:null},
    upProg:0,
    toast:{show:false,text:'',type:'success'},
    confirm:{show:false,title:'',message:'',onConfirm:()=>{},okText:'Confirm'},

    async init(){try{const r=await Promise.all([fetch('/api/index'),fetch('/api/moments'),fetch('/api/insights')]);const d=await Promise.all(r.map(x=>x.json()));this.build(d[0],d[1],d[2])}catch(e){this.flash('Load failed','error')}},
    async refreshAll(){this.loading=true;try{const r=await Promise.all([fetch('/api/index'),fetch('/api/moments'),fetch('/api/insights')]);const d=await Promise.all(r.map(x=>x.json()));this.build(d[0],d[1],d[2]);this.flash('Updated')}finally{this.loading=false}},
    build(idx,mom,ins){
        // Build friendly person display names
        this.people=Object.values(idx?.person_registry||{}).map(p=>({
            ...p,
            display:p.name||p.id.replace('PERSON_','Person ')
        })).sort((a,b)=>b.face_count-a.face_count);
        // Replace raw IDs in insights with friendly names
        this.insights=(ins||[]).map(i=>{
            let msg=i.message||'';
            // Replace Person ID patterns with display names
            Object.values(idx?.person_registry||{}).forEach(p=>{
                if(p.id.includes('PERSON_')&&p.name){
                    msg=msg.split(p.id).join(p.name);
                }
            });
            return{...i,message:msg};
        });
        this.allPhotos=(idx.image_catalog||[]).map(p=>{p.person_ids=[...(new Set((p.assignments||[]).filter(a=>a.person_id).map(a=>a.person_id)))];return p});
        this.moments=mom||[];
        this.topPhotos=[...this.allPhotos.filter(p=>p.quality_score>6)].sort((a,b)=>(b.quality_score||0)-(a.quality_score||0)).slice(0,10);
        this.$nextTick(()=>lucide.createIcons());
        // Preload avatars
        this.people.forEach(async p=>{if(p.best_face_hash){try{const r=await fetch('/api/face-thumb/'+p.best_face_hash);if(r.ok)p.avatarUrl=URL.createObjectURL(await r.blob())}catch(e){}}});
    },
    // Nav & UI helpers
    flash(t,type='success'){this.toast={show:true,text:t,type};setTimeout(()=>this.toast.show=false,3000)},
    confirmAction(msg,action){
        const c=this.confirm;
        c.message=msg;c.okText=action.startsWith('delete')?'Delete':'OK';
        c.onConfirm=async()=>{
            if(action==='regenerateMoments'){await fetch('/api/moments/regenerate',{method:'POST'});this.flash('Moments regenerated');await this.refreshAll();}
            else if(action==='clearFaces'){await fetch('/api/moments/regenerate',{method:'POST'});this.flash('Face cache cleared');}
            else if(action.startsWith('deleteMoment::')){const id=action.split('::')[1];await fetch('/api/moments/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({moment_id:id})});this.flash('Moment deleted');await this.refreshAll();}
            else if(action.startsWith('deletePerson::')){const id=action.split('::')[1];await fetch('/api/people/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({person_id:id})});this.flash('Person deleted');await this.refreshAll();}
            else if(action.startsWith('mergeInit::')){const src=action.split('::')[1];this.mergeSource=src;this.mergePending=true;this.flash('Now tap another person to complete the merge','success');}
        };
        c.show=true;
    },

    // Moment editing
    editMomentLabel(m){this.momentEdit={show:true,action:'Rename',input:m.label||'',target:m};},
    async doMomentEdit(){
        const m=this.momentEdit.target;if(!m)return;this.momentEdit.show=false;
        await fetch('/api/moments/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({moment_id:m.id,new_label:this.momentEdit.input})});
        this.flash('Label updated');await this.refreshAll();
    },
    showMomentMenu(m){this.moments.forEach(x=>x.__menu=false);m.__menu=true;},

    // Moment gallery
    openMomentGallery(m){this.mgEdit=false;this.mgMoment=m;this.mgPhotos=(m.member_paths||[]).map(fp=>this.allPhotos.find(p=>p.file_path===fp)||{file_path:fp,caption:'',quality_score:0,analyzed_at:''});this.mgOpen=true},
    async setMomentCover(i){if(!this.mgMoment)return;const fp=this.mgPhotos[i]?.file_path;if(fp){await fetch('/api/moments/cover',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({moment_id:this.mgMoment.id,file_path:fp})});this.flash('Cover updated');await this.refreshAll();}},
    async removeMomentPhoto(i){if(!this.mgMoment)return;const fp=this.mgPhotos[i]?.file_path;if(fp){await fetch('/api/moments/remove-photo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({moment_id:this.mgMoment.id,file_path:fp})});this.flash('Photo removed');this.mgPhotos.splice(i,1);if(this.mgPhotos.length===0)this.mgOpen=false;await this.refreshAll();}},

    // Lightbox
    lightboxOpen(id){this.lbOpen=true;this.lbIdx=id;this.lbPhotos=this.allPhotos;this.lbDetail=true;this.$nextTick(()=>lucide.createIcons());},
    lightboxOpenFromList(idx){this.lbOpen=true;this.lbIdx=idx;this.lbPhotos=this.allPhotos;this.lbDetail=true;this.$nextTick(()=>lucide.createIcons());},
    lbFromPhotos(arr,i){this.lbPhotos=arr;this.lbIdx=i;this.lbOpen=true;this.lbDetail=true;this.pgOpen=false;this.mgOpen=false;this.$nextTick(()=>lucide.createIcons());},
    get lbPhoto(){return this.lbPhotos[this.lbIdx]||null},
    get lbCurUrl(){const p=this.lbPhotos[this.lbIdx]||{};return'/images/'+(p.file_path||'').split('/').pop()},
    get lbPhotoPeople(){return this.lbPhoto?this.people.filter(pp=>(this.lbPhoto.person_ids||[]).includes(pp.id)):[]},
    lbPrev(){if(this.lbIdx>0){this.lbIdx--;this.lbDetail=true}},
    lbNext(){if(this.lbIdx<this.lbPhotos.length-1){this.lbIdx++;this.lbDetail=true}},

    // Swipe navigation (only works when not zoomed)
    lbSwipe(e){
        if(this.lbZ.s>1.05)return; // Swipe disabled when zoomed in
        const d=this.lbST-(e.changedTouches?.[0].clientX||0);
        if(Math.abs(d)>50){d>0?this.lbNext():this.lbPrev();}
    },

    // Zoom handlers: pinch, scroll wheel, double-tap
    lbZoomStart(e){
        this.lbMenuOpen=false;
        if(e.touches&&e.touches.length===2){
            // Pinch start
            this.lbZ.pinchDist=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
            this.lbZ.pinchScale=this.lbZ.s;
        }else{
            const t=e.touches?e.touches[0]:e;
            this.lbZ.panning=this.lbZ.s>1;
            this.lbZ.startX=t.clientX-this.lbZ.x;
            this.lbZ.startY=t.clientY-this.lbZ.y;
        }
    },
    lbZoomMove(e){
        const z=this.lbZ;
        if(e.touches&&e.touches.length===2){
            const dist=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
            const newScale=Math.max(z.min,Math.min(z.max,z.pinchScale*(dist/z.pinchDist)));
            if(newScale!==z.s){z.s=newScale;z.panning=false;}
        }else if(z.s>1&&z.panning){
            const t=e.touches?e.touches[0]:e;
            z.x=t.clientX-z.startX;z.y=t.clientY-z.startY;
            e.preventDefault();
        }
    },
    lbZoomEnd(e){
        const z=this.lbZ;z.panning=false;
        if(z.s<=1.05){z.s=1;z.x=0;z.y=0;}
    },
    lbWheel(e){
        const z=this.lbZ;
        const delta=-e.deltaY/200;
        const newScale=Math.max(z.min,Math.min(z.max,z.s+delta));
        if(newScale>1){
            z.x-=(e.clientX-e.target.clientWidth/2)*delta*0.5;
            z.y-=(e.clientY-e.target.clientHeight/2)*delta*0.5;
        }
        z.s=newScale;
        if(z.s<=1.05){z.s=1;z.x=0;z.y=0;}
    },
    lbDoubleTap(e){
        const z=this.lbZ;const now=Date.now();
        if(now-z.lastTap<300){
            if(z.s>1){z.s=1;z.x=0;z.y=0;}
            else{
                const rect=e.target.getBoundingClientRect();
                z.x=-(e.clientX-rect.left-rect.width/2)*(z.max-1)/z.max*0.5;
                z.y=-(e.clientY-rect.top-rect.height/2)*(z.max-1)/z.max*0.5;
                z.s=Math.min(z.max,z.min+2);
            }
        }
        z.lastTap=now;
    },

    // Lightbox photo management
    lbSaveCaption(){
        const p=this.lbPhoto;if(!p)return;
        fetch('/api/photos/caption',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file_path:p.file_path,caption:this.lbCaption})});
        p.caption=this.lbCaption;
        [this.allPhotos,this.pgPhotos,this.mgPhotos,this.tlPhotos,this.lbPhotos].forEach(arr=>{const x=arr.find(pp=>pp.file_path===p.file_path);if(x)x.caption=p.caption;});
        this.lbCaptionEdit=false;this.lbMenuOpen=false;this.flash('Caption saved');
    },
    lbEditCaption(){if(!this.lbPhoto)return;this.lbCaptionEdit=true;this.lbCaption=(this.lbPhoto.caption||'');},
    lbMovePhoto(){if(!this.lbPhoto)return;this.lbMoveShow=true;},
    async doMovePhoto(targetFolder){
        const p=this.lbPhoto;if(!p)return;
        try{
            await fetch('/api/photos/move',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file_path:p.file_path,target_folder:targetFolder})});
            this.lbPhotos.splice(this.lbIdx,1);
            if(this.lbIdx>=this.lbPhotos.length)this.lbIdx=Math.max(0,this.lbPhotos.length-1);
            this.lbMoveShow=false;
            [this.allPhotos,this.pgPhotos,this.mgPhotos,this.tlPhotos].forEach(arr=>{const i=arr.findIndex(x=>x.file_path===p.file_path);if(i!==-1)arr.splice(i,1);});
            if(this.lbPhotos.length===0)this.lbOpen=false;
            this.flash('Photo moved to '+targetFolder.split('/').pop());
        }catch(e){this.flash('Move failed','error');this.lbMoveShow=false}
    },
    lbDeletePhoto(){if(!this.lbPhoto)return;this.lbDeleteShow=true;},
    async doDeletePhoto(){
        const p=this.lbPhoto;if(!p)return;
        try{
            await fetch('/api/photos/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file_path:p.file_path})});
            this.lbPhotos.splice(this.lbIdx,1);
            if(this.lbIdx>=this.lbPhotos.length)this.lbIdx=Math.max(0,this.lbPhotos.length-1);
            this.lbDeleteShow=false;
            [this.allPhotos,this.pgPhotos,this.mgPhotos,this.tlPhotos].forEach(arr=>{const i=arr.findIndex(x=>x.file_path===p.file_path);if(i!==-1)arr.splice(i,1);});
            if(this.lbPhotos.length===0)this.lbOpen=false;
            this.flash('Photo deleted');
        }catch(e){this.flash('Delete failed','error');this.lbDeleteShow=false}
    },

    // People
    viewPersonGallery(p){this.pgPerson=p;this.pgPhotos=this.allPhotos.filter(x=>(x.person_ids||[]).includes(p.id)).sort((a,b)=>(b.analyzed_at||'').localeCompare(a.analyzed_at||''));this.pgOpen=true},
    viewTimeline(p){this.tlPerson=p;this.tlPhotos=this.allPhotos.filter(x=>(x.person_ids||[]).includes(p.id)).sort((a,b)=>(a.analyzed_at||'').localeCompare(b.analyzed_at||''));this.tlOpen=true},
    openRename(p){this.rnId=p.id;this.rnInput=p.display||'';this.rnOpen=true;this.$nextTick(()=>{if(this.$refs.rnField)this.$refs.rnField.focus()})},
    async doRename(){
        if(!this.rnInput.trim())return;
        try{await fetch('/api/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({person_id:this.rnId,new_name:this.rnInput})});this.flash('Renamed to "'+this.rnInput+'"');this.rnOpen=false;await this.refreshAll();}catch(e){this.flash('Rename failed','error')}
    },

    // Merge: tap another person to complete
    handleMergeTap(p){
        if(this.mergePending&&this.mergeSource&&this.mergeSource!==p.id){
            fetch('/api/merge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_id:this.mergeSource,target_id:p.id})}).then(()=>{
                this.flash('Merged into '+p.display);this.mergeSource=null;this.mergePending=false;
                this.refreshAll();
            }).catch(()=>this.flash('Merge failed','error'));
            return true;
        }return false;
    },

    // Search
    async doSearch(){
        if(!this.searchQ.trim()){this.searchRes=null;return}
        try{const r=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:this.searchQ,top_k:20})});this.searchRes=(await r.json()).results||[];}catch(e){this.searchRes=[]}
    },

    // Add moment
    async doAddMoment(){
        const label=this.newMomentLabel.trim();
        try{
            if(label){
                const photos=this.allPhotos.slice(0,6).map(p=>p.file_path);
                await fetch('/api/moments/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({label,photo_paths:photos})});
            }else{
                await fetch('/api/moments/regenerate',{method:'POST'});
            }
            this.addMomentOpen=false;
            await this.refreshAll();
            this.flash(label?'Moment created':'Moments regenerated');
        }catch(e){this.flash('Failed to create','error');this.addMomentOpen=false}
    },

    // Upload
    async handleUpload(e){
        const files=Array.from(e.target.files);if(!files.length)return;this.upProg=5;
        for(let i=0;i<files.length;i++){const fd=new FormData();fd.append('file',files[i]);try{await fetch('/api/upload',{method:'POST',body:fd});this.upProg=Math.round(((i+1)/files.length)*95)}catch(e){this.flash('Upload failed: '+files[i]?.name,'error')}}
        this.upProg=100;this.flash(files.length+' file'+(files.length>1?'s':'')+' uploaded!');
        setTimeout(()=>this.upProg=0,2000);await this.refreshAll();e.target.value='';
    },

    // Helpers
    imgThumb(i){return'/images/'+((i?.file_path||i?.cover_image||'').split('/').pop())},
    fmtDate(d){try{return new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}catch(e){return''+d}},
    getMomentDateRange(m){
        if(!m?.member_paths)return'Captured recently';
        try{const ds=m.member_paths.map(fp=>{const ph=this.allPhotos.find(x=>x.file_path===fp);return ph?.analyzed_at?new Date(ph.analyzed_at).getTime():0}).filter(d=>d>0);if(!ds.length)return'Captured recently';const a=new Date(Math.min(...ds)),b=new Date(Math.max(...ds));const f=a.toLocaleDateString('en-US',{month:'short',day:'numeric'}),l=b.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});return a.toDateString()===b.toDateString()?f:f+' — '+l}catch(e){return'Captured recently'}
    },
    getPhotoIdx(p){return this.allPhotos.findIndex(x=>x.file_path===p.file_path)},
    findPhotoIdx(fp){return this.allPhotos.findIndex(x=>x.file_path===fp)},
    postAction(url,msg){fetch(url,{method:'POST'}).then(()=>this.flash(msg)).catch(()=>this.flash('Failed','error'));this.refreshAll();}
}}
</script>
</body>
</html>
