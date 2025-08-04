class Stat {
    constructor( name ) {
        this.lines = 0;
        this.name = name ;
        //  Calculation from Wikipedia article
        this.n = 0;
        this.Q = 0.;
        this.A = 0.;
        this.max = null ;
        this.min = null ;
    }
    add( lines ) {
        this.lines += 1;
        lines.forEach( x => {
            this.n += 1 ;
            this.Q += (this.n-1)*(x-this.A)**2/this.n
            this.A += (x-this.A)/this.n ;
            if ( this.n == 1 ) {
                this.max = x ;
                this.min = x ;
            } else {
                this.max = Math.max( x, this.max ) ;
                this.min = Math.min( x, this.min ) ;
            }
        });
    }
    Max() {
        return this.max ;
    }
    Min() {
        return this.min ;
    }
    Lines() {
        return this.lines ;
    }
    N() {
        return this.n;
    }
    Avg() {
        return this.A ;
    }
    Std() {
        return Math.sqrt( this.Q/this.n ) ;
    }
    Name() {
        return this.name ;
    }
}
class StatList {
    constructor( data ) {
        this.all = new Stat("All") ;
        this.list = {} ;
        data.forEach( dline => this.addline(dline) );
    }
    addline( dline ) {
        const numbers = ((dline[2].match(/-?(\d+\.?\d*|\.?\d+)/g))??[]).map(Number) ;
        this.all.add(numbers);
        const key = dline[1] ;
        if ( !(key in this.list) ) {
            this.list[key] = new Stat(key) ;
        }
        this.list[key].add(numbers);
    }
    All() {
        return this.all ;
    }
    Keys() {
        return Object.keys(this.list) ;
    }
    Stat(key) {
        return this.list[key] ;
    }
}
class Swipe {
    constructor() {
        this.thresholdX = 100;
        this.thresholdY = 31;
        window.addEventListener('touchstart', (event)=>this.start(event) ); 
        window.addEventListener('touchend',   (event)=>this.stop(event)  ); 
    }
    start( event ) {
        this.initialX = event.touches[0].clientX;
        this.initialY = event.touches[0].clientY;
    }
    stop() {
        const deltaX = this.initialX - event.changedTouches[0].clientX;
        const deltaY = this.initialY - event.changedTouches[0].clientY;
        if ( Math.abs(deltaY) < this.thresholdY ) {
            if ( deltaX > this.thresholdX ) {
                let copy = new Date(globals.daystart.valueOf());
                NewDate( new Date(copy.setDate(copy.getDate()-1)) );
            } else if ( deltaX < -this.thresholdX ) {
                let copy = new Date(globals.daystart.valueOf());
                NewDate( new Date(copy.setDate(copy.getDate()+1)) );
            }
        }
    }
}
function YYYYMMDD(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}
function NewDate(date) {
    const url = new URL(location.href);
    url.searchParams.set('date', YYYYMMDD(date));
    url.searchParams.set('type', globals.page_type);
    location.assign(url.search);
}
function NewType(ntype) {
    const url = new URL(location.href);
    url.searchParams.set('date', YYYYMMDD(globals.daystart));
    url.searchParams.set('type', ntype);
    location.assign(url.search);
}
class Data {
    constructor() {
        this.table = document.getElementById("table");
        this.table.innerHTML="";
        this.thead = this.table.createTHead().insertRow(-1);
        this.tbody = this.table.createTBody();
    }
    Show() {
        this.table.classList.add("dataTable");
        this.SortOn() ;
        this.CreateDataTable() ;
    }          
    SortOn( column=null ){
        const so = sessionStorage.getItem("sortorder");
        let sortorder = [0,1] ;
        if ( so != null ) {
            sortorder = JSON.parse(so);
        }
        if ( column != null ) {
            if ( column==sortorder[0] ) {
                sortorder[1] = -sortorder[1] ;
            } else {
                sortorder = [column, 1];
            }
        }
        if ( sortorder[1] > 0 ) {
            globals.dayData.sort( (r1,r2) => r1[sortorder[0]].localeCompare(r2[sortorder[0]]) );
        } else {
            globals.dayData.sort( (r2,r1) => r1[sortorder[0]].localeCompare(r2[sortorder[0]]) );
        }
        sessionStorage.setItem("sortorder",JSON.stringify(sortorder));
    }
    CreateDataTable() {
        const sym=(i,s0,s1)=>{
            if (i!=s0){return "&nbsp";}
            if ( s1>0){return "&uarr;";}
            return "&darr;";
        }
        const sortorder = JSON.parse(sessionStorage.getItem("sortorder"));
        ["Time","Source","Data"].forEach( (h,i) => this.thead.insertCell(-1).innerHTML=`<span onclick="SortOn(${i})"><B>${h}&nbsp;${sym(i,sortorder[0],sortorder[1])}</B></span>` );
        globals.dayData.forEach( r => this.AddRow( r ) );
    }
    AddRow( row_data ) {
        const row = this.tbody.insertRow(-1);
        row_data.forEach( d => row.insertCell(-1).innerHTML=d );
    }
}
class Statistics extends Data {
    Show() {
        this.table.classList.add("statTable");
        ["Source","Types","Values"].forEach( (h,i) => this.thead.insertCell(-1).innerHTML=`<B>${h}</B>` );
        const statData = new StatList( globals.dayData ) ;
        statData.Keys().map( k=> statData.Stat(k)).forEach( s => this.AddStat( s ) ) ;
        this.AddStat( statData.All() );
    }                  
    AddStat( stat ) {
        this.AddRow( [`<B>${stat.Name()}</B>`, "Lines, Readings", `${stat.Lines()}, ${stat.N()}`]);
        this.AddRow( ["", "Avg (Std)", (stat.N()==0)?"":`${stat.Avg().toFixed(2)} (${stat.Std().toFixed(2)})`]);
        this.AddRow( ["", "Range", (stat.N()==0)?"":`${stat.Min()} &mdash; ${stat.Max()}`]);
    }
}
function TestDate(x) {
    switch (x.cellType) {
        case 'day':
            return globals.goodDays.includes(YYYYMMDD(x.date));
        case 'month':
            return globals.goodMonths.includes(YYYYMMDD(x.date));
        case 'year':
            return globals.goodYears.includes(YYYYMMDD(x.date));
        default:
            return false;
    }
}
class Plot {
    constructor() {
        const div = document.getElementById("contentarea") ;
        this.canvas = document.getElementById("graphcanvas");

        this.canvas.width = div.offsetWidth ;
        this.width = this.canvas.width ;
        this.canvas.height = div.offsetHeight ;
        this.height = this.canvas.height ;
        
        this.ctx = this.canvas.getContext('2d');
        
        if ( 'orientation' in screen ) {
            screen.orientation.addEventListener('change', () => NewType('plot') );
        }
        this.colors=["red","darkorange","purple","green","darkgreen","pink","brown","darkgray","dodgerblue"];
    }
    Show() {
        this.data();
        this.legend();
        this.setup();
        this.plot();
    }
    
    data() {
        this.Ys={};
        this.select={};
        globals.dayData.forEach( row => {
            const time= ((row[0].match(/(\d+)/g))??["0"]).map(Number).reduceRight((t,x)=>x+t/60) ;
            const key = row[1] ;
            if ( !(key in this.Ys) ) {
                this.Ys[key] = [] ;
                this.select[key] = true;
            }
            const numbers = ((row[2].match(/-?(\d+\.?\d*|\.?\d+)/g))??[]).map(Number) ;
            numbers.forEach( n => this.Ys[key].push([time,n]));
        });
    }
    legend() {
		const legend = document.getElementById("legend");
		Object.keys(this.select).forEach( (key,i) =>{
			const le = document.createElement("label");
			le.style.color=this.colors[i];
			le.innerText=key;
			const ch = document.createElement("input");
			ch.type="checkbox";
			ch.style.color=this.colors[i];
			ch.checked = this.select[key] ;
			ch.onchange=()=>{
				this.select[key]=ch.checked;
				this.filter();
				this.setup();
				this.plot();
			};
			le.appendChild(ch);
			legend.appendChild(le);
		});
    }
    filter() {
        this.maxY = -Infinity ;
        this.minY = Infinity ;
        Object.keys(this.select).filter(key=>this.select[key]).this.Ys[key].forEach( r=> {
			this.maxY=Math.max(this.maxY,r[1]);
			this.minY=Math.min(this.minY,r[1]);
		});
        this.padX = 10;
        this.padY = 10 ;
        this.X0 = 0.;
        this.X1 = 24.;
        this.scaleX = (this.width-2*this.padX)/(this.X1-this.X0) ;
        this.Y1 = Math.round( this.maxY + 1 );
        this.Y0 = Math.round( this.minY - 2 );
        this.scaleY = (this.height-2*this.padY)/(this.Y1-this.Y0) ;
	}
    setup() {
        this.ctx.fillStyle = "white" ;
        this.ctx.fillRect(0,0,this.width,this.height) ;
        this.ctx.strokeStyle = "lightgray" ;
        this.ctx.lineWidth = 1 ;
        for ( let time = this.X0; time <= this.X1 ; time += 1 ) {
            // grid
            this.ctx.beginPath() ;
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
            this.ctx.stroke() ;
        }
        this.ctx.lineWidth = 2 ;
        for ( let time = this.X0; time <= this.X1 ; time += 2 ) {
            // grid
            this.ctx.beginPath() ;
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
            this.ctx.stroke() ;
        }
        this.ctx.lineWidth = 4 ;
        for ( let time = this.X0; time <= this.X1 ; time += 4 ) {
            // grid
            this.ctx.beginPath() ;
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
            this.ctx.stroke() ;
        }
        this.ctx.lineWidth = 1 ;
        for ( let temp = this.Y0; temp <= this.Y1 ; temp += 1 ) {
            // grid
            this.ctx.beginPath() ;
            this.ctx.moveTo( this.X(this.X0),this.Y(temp) ) ;
            this.ctx.lineTo( this.X(this.X1),this.Y(temp) ) ;
            this.ctx.stroke() ;
        }
        this.ctx.font = `${Math.round(this.scaleY/2)}px san serif` ;
        this.ctx.fillStyle = "gray" ;
        for ( let temp = this.Y0; temp <= this.Y1 ; temp += 1 ) {
            this.ctx.fillText(Number(temp).toFixed(0),this.X(this.X0),this.Y(temp))
        }
        this.ctx.font = `${this.padX}px san serif` ;
        this.ctx.fillStyle = "gray" ;
        for ( let time = this.X0+4; time < this.X1 ; time += 4 ) {
            this.ctx.fillText(Number(time).toFixed(0),this.X(time),this.height)
        }
    }
    plot() {
        this.ctx.lineWidth=5;
        Object.keys(this.Ys).forEach( (k,i) => {
            this.ctx.strokeStyle=this.colors[i] ;
            this.Ys[k].forEach( xy => {
                this.ctx.beginPath() ;
                this.ctx.arc(this.X(xy[0]),this.Y(xy[1]),5,0,2*Math.PI);
                this.ctx.stroke();
            });
        });
    }
    X(time) {
        return this.padX + (time-this.X0)*this.scaleX ;
    }
    Y(temp) {
        return this.padY + (this.Y1-temp)*this.scaleY ;
    }
}
window.onload = () => {
    globalThis.dp = new AirDatepicker("#new_cal", {
            onSelect(x) {NewDate(x.date)},
            isMobile:true,
            buttons:[{content:'Today',onClick:(dp)=>NewDate(new Date())}],
            selectedDates:[globals.daystart],
            onRenderCell(x) { if (TestDate(x)) { return {classes:'present'};} },
    } ) ;
    var swipe = new Swipe() ;
    document.getElementById("date").innerHTML = globals.header_date;
    document.getElementById("time").innerHTML = globals.header_time;
    document.getElementById("showdate").innerHTML = globals.daystart.toLocaleDateString();
    switch (globals.page_type) {
        case "stat":
            new Statistics().Show() ;
            break ;
        case "plot":
            document.querySelectorAll(".non-plot").forEach( x=>x.style.display="none");
            document.querySelectorAll(".yes-plot").forEach( x=>x.style.display="block");
            new Plot().Show();
            break ;
        default: // "data"
            new Data().Show() ;
            break ;
    }
    
}

