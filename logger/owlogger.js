/* owlogger
 * one-wire logging
 * See https://github.con/alfille/owlogger
 * Paul H Alfille 2025 MIT licence */

/* jshint esversion: 11 */

class Cumulative {
    constructor( name ) {
        this.lines = 0;
        this.name = name ;
        //  Calculation from Wikipedia article
        this.n = 0;
        this.Q = 0;
        this.A = 0;
        this.max = null ;
        this.min = null ;
    }
    add( lines ) {
        this.lines += 1;
        lines.forEach( x => {
            this.n += 1 ;
            this.Q += (this.n-1)*(x-this.A)**2/this.n ;
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
class StatCalc {
    constructor( data ) {
        this.all = new Cumulative("All") ;
        this.list = {} ;
        data.forEach( dline => this.addline(dline) );
    }
    addline( dline ) {
        const numbers = ((dline[2].match(/-?(\d+\.?\d*|\.?\d+)/g))??[]).map(Number) ;
        this.all.add(numbers);
        const key = dline[1] ;
        if ( !(key in this.list) ) {
            this.list[key] = new Cumulative(key) ;
        }
        this.list[key].add(numbers);
    }
    All() {
        return this.all ;
    }
    Keys() {
        return Object.keys(this.list) ;
    }
    Cumulative(key) {
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
                JumpTo.date( new Date(copy.setDate(copy.getDate()-1)) );
            } else if ( deltaX < -this.thresholdX ) {
                let copy = new Date(globals.daystart.valueOf());
                JumpTo.date( new Date(copy.setDate(copy.getDate()+1)) );
            }
        }
    }
}
class JumpTo {
    static YYYYMMDD(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    static date(date) {
        this.jump( date, globals.page_type ) ;
    }
    static type(ntype) {
        this.jump( globals.daystart, ntype ) ;
    }
    static jump(date,ntype) {
        const url = new URL(location.href);
        url.searchParams.set('date', this.YYYYMMDD(date));
        url.searchParams.set('type', ntype);
        location.assign(url.search);
    }
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
        this.ShowDataTable() ;
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
    ShowDataTable() {
        const sym=(i,s0,s1)=>{
            if (i!=s0){return "&nbsp";}
            if ( s1>0){return "&uarr;";}
            return "&darr;";
        };
        this.thead.innerHTML="";
        this.tbody.innerHTML="";
        const sortorder = JSON.parse(sessionStorage.getItem("sortorder"));
        ["Time","Source","Data"].forEach( (h,i) => {
            const t = this.thead.insertCell(-1) ;
            t.innerHTML=`<B>${h}&nbsp;${sym(i,sortorder[0],sortorder[1])}</B>`;
            t.onclick=()=>{
                this.SortOn(i);
                this.ShowDataTable();
            };
        });
        globals.dayData.forEach( r => this.ShowRow( r ) );
    }
    ShowRow( row_data ) {
        const row = this.tbody.insertRow(-1);
        row_data.forEach( d => row.insertCell(-1).innerHTML=d );
    }
}
class Stat extends Data {
    Show() {
        this.table.classList.add("statTable");
        this.statData = new StatCalc( globals.dayData ) ;
        this.ShowStatTable();
    }                  
    ShowStatTable() {
        ["Source","Types","Values"].forEach( (h,i) => this.thead.insertCell(-1).innerHTML=`<B>${h}</B>` );
        this.statData.Keys().map( k=> this.statData.Cumulative(k)).forEach( s => this.ShowStat( s ) ) ;
        this.ShowStat( this.statData.All() );
    }                  
    ShowStat( stat ) {
        this.ShowRow( [`<B>${stat.Name()}</B>`, "Lines, Readings", `${stat.Lines()}, ${stat.N()}`]);
        this.ShowRow( ["", "Avg (Std)", (stat.N()==0)?"":`${stat.Avg().toFixed(2)} (${stat.Std().toFixed(2)})`]);
        this.ShowRow( ["", "Range", (stat.N()==0)?"":`${stat.Min()} &mdash; ${stat.Max()}`]);
    }
}
class Plot {
    constructor() {
        const div = document.getElementById("contentarea") ;
        this.canvas = document.getElementById("graphcanvas");

        this.canvas.width = div.clientWidth ;
        this.width = this.canvas.width ;
        this.canvas.height = div.clientHeight ;
        this.height = this.canvas.height ;
        
        this.ctx = this.canvas.getContext('2d');
        this.jump() ;
        this.colors=["#c20000","#3564B1","#7e00c2","#007031","#B33E00","#5D7000","#1700c2","#006f9e","#c20067"];
    }
    jump() {
        if ( 'orientation' in screen ) {
            screen.orientation.addEventListener('change', () => JumpTo.type('plot') );
        }
	}
    Show() {
        this.data();
        this.legend();
        this.filter();
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
            const bu = document.createElement("button");
            bu.style.backgroundColor=this.colors[i];
            bu.classList.add("blegend");
            bu.innerHTML=`&#9949;&nbsp${key}`;
            bu.onclick=()=>{
                if (this.select[key]) {
                    bu.innerHTML=`&#9634;&nbsp;${key}`;
                    this.select[key]=false;
                } else {
                    bu.innerHTML=`&#9949;&nbsp;${key}`;
                    this.select[key]=true;
                }
                this.filter();
                this.setup();
                this.plot();
            };
            legend.appendChild(bu);
        });
    }
    Xlimits() {
        this.X0 = 0;
        this.X1 = 24;
	}
    filter() {
        this.maxY = -Infinity ;
        this.minY = Infinity ;
        Object.keys(this.select).filter(key=>this.select[key]).forEach( key=>this.Ys[key].forEach( r=> {
            this.maxY=Math.max(this.maxY,r[1]);
            this.minY=Math.min(this.minY,r[1]);
        }));
        this.padX = 10;
        this.padY = 10;
        this.Xlimits() ;
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
        this.ctx.beginPath() ;
        for ( let time = this.X0; time <= this.X1 ; time += 1 ) {
            // vert
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
        }
        for ( let temp = this.Y0; temp <= this.Y1 ; temp += 1 ) {
            // horz
            this.ctx.moveTo( this.X(this.X0),this.Y(temp) ) ;
            this.ctx.lineTo( this.X(this.X1),this.Y(temp) ) ;
        }
        this.ctx.stroke() ;
        
        this.ctx.lineWidth = 2 ;
        this.ctx.beginPath() ;
        for ( let time = this.X0; time <= this.X1 ; time += 2 ) {
            // 2 hr
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
        }
        this.ctx.stroke() ;
        
        this.ctx.lineWidth = 4 ;
        this.ctx.beginPath() ;
        for ( let time = this.X0; time <= this.X1 ; time += 4 ) {
            // 4 hr
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
        }
        this.ctx.stroke() ;
        
        this.ctx.font = `${this.scaleY/2}px san serif` ;
        this.ctx.fillStyle = "gray" ;
        for ( let temp = this.Y0; temp <= this.Y1 ; temp += 1 ) {
            this.ctx.fillText(Number(temp).toFixed(0),this.X(this.X0),this.Y(temp)) ;
        }
        this.ctx.font = `${this.scaleX}px san serif` ;
        this.ctx.fillStyle = "gray" ;
        for ( let time = this.X0+4; time < this.X1 ; time += 4 ) {
            this.ctx.fillText(Number(time).toFixed(0),this.X(time),this.Y(this.Y0)+0.5);
        }
    }
    plot() {
        this.ctx.lineWidth=3;
        Object.keys(this.Ys).forEach( (k,i) => {
            if ( this.select[k] ) {
                this.ctx.strokeStyle=this.colors[i] ;
                this.ctx.lineWidth=3;
                this.ctx.beginPath() ;
                this.Ys[k].forEach( xy => {
                    const x = this.X(xy[0]);
                    const y = this.Y(xy[1]);
                    this.ctx.moveTo(x,y);
                    this.ctx.arc(x,y,4,0,2*Math.PI);
                });
                this.ctx.stroke();
            }
        });
    }
    X(time) {
        return this.padX + (time-this.X0)*this.scaleX ;
    }
    Y(temp) {
        return this.padY + (this.Y1-temp)*this.scaleY ;
    }
}
class Week extends Plot {
    jump() {
        if ( 'orientation' in screen ) {
            screen.orientation.addEventListener('change', () => JumpTo.type('week') );
        }
	}
    Xlimits() {
        this.X0 = 0;
        this.X1 = 7;
	}
    data() {
        this.Ys={};
        this.select={};
        globals.dayData.forEach( row => {
            const time= Number(row[0]) ;
            const key = row[1] ;
            if ( !(key in this.Ys) ) {
                this.Ys[key] = [] ;
                this.select[key] = true;
            }
            const numbers = ((row[2].match(/-?(\d+\.?\d*|\.?\d+)/g))??[]).map(Number) ;
            numbers.forEach( n => this.Ys[key].push([time,n]));
        });
    }
    setup() {
        this.ctx.fillStyle = "white" ;
        this.ctx.fillRect(0,0,this.width,this.height) ;
        this.ctx.strokeStyle = "lightgray" ;
        
        this.ctx.lineWidth = 1 ;
        this.ctx.beginPath() ;
        for ( let time = this.X0; time <= this.X1 ; time += .25 ) {
            // vert
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
        }
        for ( let temp = this.Y0; temp <= this.Y1 ; temp += 1 ) {
            // horz
            this.ctx.moveTo( this.X(this.X0),this.Y(temp) ) ;
            this.ctx.lineTo( this.X(this.X1),this.Y(temp) ) ;
        }
        this.ctx.stroke() ;
        
        this.ctx.lineWidth = 2 ;
        this.ctx.beginPath() ;
        for ( let time = this.X0; time <= this.X1 ; time += .5 ) {
            // 12 hr
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
        }
        this.ctx.stroke() ;
        
        this.ctx.lineWidth = 4 ;
        this.ctx.beginPath() ;
        for ( let time = this.X0; time <= this.X1 ; time += 1 ) {
            // day
            this.ctx.moveTo( this.X(time),this.Y(this.Y0) ) ;
            this.ctx.lineTo( this.X(time),this.Y(this.Y1) ) ;
        }
        this.ctx.stroke() ;
        
        this.ctx.font = `${this.scaleY/2}px san serif` ;
        this.ctx.fillStyle = "gray" ;
        for ( let temp = this.Y0; temp <= this.Y1 ; temp += 1 ) {
            this.ctx.fillText(Number(temp).toFixed(0),this.X(this.X0),this.Y(temp)) ;
        }
        this.ctx.font = `${this.scaleX}px san serif` ;
        this.ctx.fillStyle = "gray" ;
        for ( let time = this.X0; time <= this.X1 ; time += 1 ) {
            this.ctx.fillText(Number(time).toFixed(0),this.X(time),this.Y(this.Y0)+0.5);
        }
    }
}
window.onload = () => {
    function TestDate(x) {
        switch (x.cellType) {
            case 'day':
                return globals.goodDays.includes(JumpTo.YYYYMMDD(x.date));
            case 'month':
                return globals.goodMonths.includes(JumpTo.YYYYMMDD(x.date));
            case 'year':
                return globals.goodYears.includes(JumpTo.YYYYMMDD(x.date));
            default:
                return false;
        }
    }
    globalThis.dp = new AirDatepicker("#new_cal", {
            onSelect(x) {JumpTo.date(x.date)},
            isMobile:true,
            buttons:[{content:'Today',onClick:(dp)=>JumpTo.date(new Date())}],
            selectedDates:[globals.daystart],
            onRenderCell(x) { if (TestDate(x)) { return {classes:'present'};} },
    } ) ;
    new Swipe() ;
    document.getElementById("date").innerHTML = globals.header_date;
    document.getElementById("time").innerHTML = globals.header_time;
    document.getElementById("showdate").innerHTML = globals.daystart.toLocaleDateString();
    switch (globals.page_type) {
        case "stat":
            document.querySelectorAll(".non-plot").forEach( x=>x.style.display="block");
            document.querySelectorAll(".yes-plot").forEach( x=>x.style.display="none");
            new Stat().Show() ;
            break ;
        case "plot":
            document.querySelectorAll(".non-plot").forEach( x=>x.style.display="none");
            document.querySelectorAll(".yes-plot").forEach( x=>x.style.display="block");
            new Plot().Show();
            break ;
        case "week":
            document.querySelectorAll(".non-plot").forEach( x=>x.style.display="none");
            document.querySelectorAll(".yes-plot").forEach( x=>x.style.display="block");
            new Week().Show();
            break ;
        default: // "data"
            document.querySelectorAll(".non-plot").forEach( x=>x.style.display="block");
            document.querySelectorAll(".yes-plot").forEach( x=>x.style.display="none");
            new Data().Show() ;
            break ;
    } 
} ;
