'use strict';

let currentReactView = null;
let waitingRoom = null;
let inGame = null;
let gameOver = null;

let localUser = null;
let localGameState = null;

function addPlayer() {
  $('#username-modal').modal('hide');
  let urlParams = new URLSearchParams(window.location.search);
  if (!urlParams.has('id')) {
      window.location.href = `${window.location.origin}/index.html`
  }
  let gameId = urlParams.get('id');
  let username = $("#username-input").val();
  if (urlParams.has('user')) {
    urlParams.set('user', username);
  } else {
    urlParams.append('user', username);
  }
  window.location.search = urlParams.toString();
  localUser = username;
  console.log('adding player');
  localSocket.send(JSON.stringify({"message": "add_player", "user": username, "id": gameId}));
}

function connect() {
  let socket = new WebSocket("wss://0ppn9ycig5.execute-api.us-east-1.amazonaws.com/alpha/");

  socket.onopen = function(e) {
      console.log('Connected')
      let urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has('id')) {
        if (urlParams.has('user')) {
          let gameId = urlParams.get('id');
          localSocket.send(JSON.stringify({"message": "add_player", "user": urlParams.get('user'), "id": gameId}));
        } else {
          $('#username-modal').modal('show');
        }
      } else {
        socket.send(JSON.stringify({"message": "new_game"}));
      }
  };

  socket.onmessage = function(event) {
    $("#centered-spinner").css("visibility", "hidden");
    console.log('Received data from server');
    let data = JSON.parse(event.data);
    localGameState = data;
    console.log(data);
    if (Array.isArray(data) && data.length === 3) {
        let urlParams = new URLSearchParams(window.location.search);
        urlParams.append('id', `game-${data[0]}-${data[1]}-${data[2]}`)
        document.location.search = urlParams.toString();
        $('#username-modal').modal('show');
    } else if (data.hasOwnProperty('error')) { 
      if (data['error'] === 'User already exists in game or game does not exist') {
        let urlParams = new URLSearchParams(window.location.search);
        urlParams.delete('user');
        window.location.search = urlParams.toString();
      }
      $('#alert-box').text(data['error']);
      $("#alert-box").removeClass('m-fadeOut');
      setTimeout(() => $("#alert-box").addClass('m-fadeOut'), 2000);
    } else if (data['game_state'] === 'waiting_room') {
      let domContainer = document.querySelector('#react-container');
      if (waitingRoom === null) {
        waitingRoom = ReactDOM.render(React.createElement(WaitingRoom, {'player' : data['player'], 'gameId': localGameState['id']}), domContainer);
      }
      waitingRoom.update(data['red_team'], data['blue_team'], data['user_name_list'], data['red_spymaster'], data['blue_spymaster']);
      currentReactView = waitingRoom;
    } else if (data['game_state'] === 'in_game') {
      let domContainer = document.querySelector('#react-container');
      if (inGame === null) {
        inGame = ReactDOM.render(React.createElement(InGame), domContainer);
      }
      inGame.update(data);
      currentReactView = inGame;
    } else if (data['game_state'] === 'post_game') {
      let domContainer = document.querySelector('#react-container');
      if (gameOver === null) {
        gameOver = ReactDOM.render(React.createElement(GameOver, {winner: data['winner']}), domContainer);
      }
      currentReactView = inGame;
    }
  };

  socket.onclose = function(event) {
    if (event.wasClean) {
      console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
    } else {
      // e.g. server process killed or network down
      // event.code is usually 1006 in this case
      console.log('[close] Connection died');
    }
    console.log(localGameState);
    if (localGameState.hasOwnProperty('last_update_time')) {
      // 15 min
      if (Date.now() - Date.UTC(localGameState['last_update_time']) < 900000) {
         localSocket = connect();
      } else {
        $('#alert-box').text("You've been disconnected due to inactivity. Please refresh to reconnect ");
        $("#alert-box").removeClass('m-fadeOut');
      }
    }
  };

  socket.onerror = function(error) {
    console.error(`[error] ${error.message}`);
  };
  return socket;
}

let localSocket = connect();

class GameOver extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
    <h1>Game over, {this.props.winner === 'blue_team'? 'Blue wins!': 'Red wins!'}</h1>
    )
  }
}

class Card extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className={`card ${this.props.cardClass}`}>
          <div className={"card-body pad-one-rem"}>
            {this.props.name}
          </div>
      </div>  
    )
  }
}

class ClueInput extends React.Component {
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleClueChange = this.handleClueChange.bind(this);
    this.handleNumChange = this.handleNumChange.bind(this);
    this.state = {clue: '', num: 1, showWarning: false, submitDisabled: true};
  }

  handleSubmit(e) {
    this.props.callback(this.state.clue, this.state.num, e);
    this.setState({clue: '', num: 1, submitDisabled: true});
    e.preventDefault();
  }

  handleClueChange(event) {
    let newClue = event.target.value;
    let newState = {clue: event.target.value, showWarning: newClue.trim().indexOf(' ') >= 0};
    newState['submitDisabled'] = this.state.num === '' || newClue === ''
    this.setState(newState);
  }

  handleNumChange(event) {
    this.setState({num: event.target.value, submitDisabled: event.target.value === '' || this.state.clue === ''});
  }

  render() {
    return (
      <form className={"form-inline"} onSubmit={this.handleSubmit}>
        <div className={"form-group mb-2"}>
          <label htmlFor={"clueBox"} className={"mr-1"}>Clue Word</label>
          <input type={"text"} className={"form-control mr-1"} id={"clueBox"} value={this.state.clue} onChange={this.handleClueChange} disabled={this.props.disabled}></input>
        </div>
        <div className={"form-group mb-2"}>
          <label htmlFor={"numberApply"} className={"mr-1"}># of Words that Apply</label>
          <input type={"number"} className={"form-control mr-1"} id={"numberApply"} value={this.state.num} onChange={this.handleNumChange} disabled={this.props.disabled}></input>
        </div>
        <button type="submit" className={"btn btn-primary mb-2"} onClick={this.handleClick} disabled={this.state.submitDisabled || this.props.disabled}>Submit</button>
        <div style={{color: "red", visibility: this.state.showWarning? "visible": "hidden"}}>Your clue has spaces. This is only allowed for proper nouns (like "New York City" or "Michael Jordan")</div>
      </form>
    )
  }
}

class InGame extends React.Component {
  constructor(props) {
    super(props);
    this.colorMapping = {
      'assassin': 'bg-dark',
      'neutral': 'bg-secondary',
      'red': 'bg-danger',
      'blue': 'bg-primary'
    };
    this.turnMapping = {
      'blue_team_guess': "Blue team's turn to guess",
      'blue_spymaster': 'Blue spymaster provides clue',
      'red_team_guess': "Red team's turn to guess",
      'red_spymaster': 'Red spymaster provides clue'
    };
    this.update = this.update.bind(this);
    this.cardOnClick = this.cardOnClick.bind(this);
    this.clueSubmitted = this.clueSubmitted.bind(this);
    this.stopGuessing = this.stopGuessing.bind(this);
  }

  update(data) {
    this.setState(data);
  }

  cardOnClick(word, e) {
    let urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('id')) {
        window.location.href = '/index.html'
        e.preventDefault();
    }
    let gameId = urlParams.get('id');
    localSocket.send(JSON.stringify({"message": "guess_word", "guess": word, "user": this.state['player'], "id": gameId}));
  }

  clueSubmitted(word, times, e) {
    let urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('id')) {
        window.location.href = '/index.html'
        e.preventDefault();
    }
    let gameId = urlParams.get('id');
    localSocket.send(JSON.stringify({"message": "provide_clue", "word": word, "times": times, "user": this.state['player'], "id": gameId}));
  }

  stopGuessing(e) {
    let urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('id')) {
        window.location.href = '/index.html'
        e.preventDefault();
    }
    let gameId = urlParams.get('id');
    localSocket.send(JSON.stringify({"message": "guess_word", "user": this.state['player'], "id": gameId}));
  }

  render() {
    let data = this.state;
    let extraText = "";
    let clueElement = null;
    let stopGuessing = null;
    if (data === null) {
      return <div></div>;
    }
    let wordCards = [];
    for (let [i, row] of data['words'].entries()) {
      let cards = [];
      for (let [j, word] of row.entries()) {
        let cardClass = 'bg-light';

        if (data['player'] !== data['red_spymaster'] && data['player'] !== data['blue_spymaster']) {
          if (data['revealed'][i][j]) {
            cardClass = this.colorMapping[data['tile_identities'][i][j]];
          }
        } else {
          cardClass = this.colorMapping[data['tile_identities'][i][j]];
        }
        let moreProps = {};
        let classes = "col one-pad";
        let team = data['red_team'].indexOf(data['player']) >= 0? 'red': 'blue';
        if (data['player'] !== data['red_spymaster'] && data['player'] !== data['blue_spymaster'] && data['turn'] === team + "_team_guess") {
          moreProps['onClick'] = this.cardOnClick.bind(this, word);
          classes += " point";
          extraText = " (you are up!)";
          stopGuessing = <button onClick={this.stopGuessing} className={"btn btn-primary"}>Stop Guessing</button>
        }
        let isSpymaster = (data['player'] === data['red_spymaster'] || data['player'] === data['blue_spymaster']);
        if (isSpymaster && data['turn'] === team + "_spymaster") {
          extraText = " (you are up!)";
          clueElement = <ClueInput callback={this.clueSubmitted}></ClueInput>
        } else if (isSpymaster) {
          clueElement = <ClueInput disabled={true}></ClueInput>
        }
        if (cardClass !== 'bg-light') {
          moreProps['style'] = {color: 'white'}
        }
        cards.push(<div className={classes} {...moreProps} key={word}><Card cardClass={cardClass} name={word}></Card></div>)
      }
      wordCards.push(<div className={"row"} key={i}>{cards}</div>);
    }
    let redClues = [];
    let blueClues = [];
    for (let [clue, num] of data['red_clues']) {
      redClues.push(<h6 key={`${clue} ${num}`}>{`${clue} ${num}`}</h6>);
    }
    for (let [clue, num] of data['blue_clues']) {
      blueClues.push(<h6 key={`${clue} ${num}`}>{`${clue} ${num}`}</h6>);
    }
    let scoreBoard = <div className={"row"}>
                      <div className={"col"}>
                        <h4>Red Clues</h4>
                        {redClues}
                      </div>
                      <div className={"col"}>
                        <h4>Blue Clues</h4>
                        {blueClues}
                      </div>
                      <div className={"col"}>
                        <h4>Cards Left</h4><br></br><h5>Red: {data['red_count_left']} Blue: {data['blue_count_left']}</h5>
                      </div>
                    </div>
    return (
      <React.Fragment>
        <div className={"row"}><div className={"col"}><h2>{this.turnMapping[data['turn']]}{extraText}</h2></div></div>
        <div>{wordCards}</div>
        {stopGuessing}
        {clueElement}
        {scoreBoard}
      </React.Fragment>
    );
  }
}

class WaitingRoom extends React.Component {
  constructor(props) {
    super(props);
    this.state = { red_team: [], blue_team: [], user_list: [], disabled: false };
    this.update = this.update.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.requestRedSpymaster = this.requestRedSpymaster.bind(this);
    this.requestBlueSpymaster = this.requestBlueSpymaster.bind(this);
    this.readyStart = this.readyStart.bind(this);
    this.startGame = this.startGame.bind(this);
  }

  update(red_team , blue_team, user_list, red_spymaster, blue_spymaster) {
    this.setState({ red_team: red_team, blue_team: blue_team, user_list: user_list, red_spymaster: red_spymaster, blue_spymaster: blue_spymaster, disabled: false })
  }

  handleClick(team, spymaster, e) {
    let red_team = this.state.red_team;
    let blue_team = this.state.blue_team;
    let red_spymaster = this.state.red_spymaster;
    let blue_spymaster = this.state.blue_spymaster;
    if (team === "random") {
      if (red_team.indexOf(this.props.player) >= 0) {
        red_team.splice(red_team.indexOf(this.props.player), 1);
      } else if (blue_team.indexOf(this.props.player) >= 0) {
        blue_team.splice(blue_team.indexOf(this.props.player), 1);
      }
      if (red_spymaster === this.props.player) {
        red_spymaster = null;
      }
      if (blue_spymaster === this.props.player) {
        blue_spymaster = null;
      }
    } else if (team === "red") {
      if (blue_spymaster === this.props.player) {
        blue_spymaster = null;
      }
      if (spymaster) {
        red_spymaster = this.props.player;
      }
      if (blue_team.indexOf(this.props.player) >= 0) {
        blue_team.splice(blue_team.indexOf(this.props.player), 1);
      }
      red_team.push(this.props.player);
    } else if (team === "blue") {
      if (red_spymaster === this.props.player) {
        red_spymaster = null;
      }
      if (spymaster) {
        blue_spymaster = this.props.player
      }
      if (red_team.indexOf(this.props.player) >= 0) {
        red_team.splice(red_team.indexOf(this.props.player), 1);
      }
      blue_team.push(this.props.player);
    }
    let newState = {red_team: red_team, blue_team: blue_team, red_spymaster: red_spymaster, blue_spymaster: blue_spymaster, disabled: true}
    if (team === "red" && spymaster) {
      newState.red_spymaster = this.props.player;
    } else if (team === "blue" && spymaster) {
      newState.blue_spymaster = this.props.player;
    }
    this.setState(newState)

    let urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('id')) {
        window.location.href = '/index.html'
        e.preventDefault();
    }
    let gameId = urlParams.get('id');
    localSocket.send(JSON.stringify({"message": "claim_team", "team": team, "spymaster": spymaster, "user": this.props.player, "id": gameId}));
  }

  requestRedSpymaster(e) {
    this.handleClick('red', true, e)
  }

  requestBlueSpymaster(e) {
    this.handleClick('blue', true, e)
  }

  readyStart() {
    let unassigned = this.state.user_list.length - this.state.red_team.length - this.state.blue_team.length;
    if (unassigned < (2 - Math.min(2, this.state.red_team.length)) + (2 - Math.min(2, this.state.blue_team.length))) {
      return false;
    }
    return true;
  }

  startGame(e) {
    let urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('id')) {
        window.location.href = '/index.html'
        e.preventDefault();
    }
    let gameId = urlParams.get('id');
    localSocket.send(JSON.stringify({"message": "start_game", "width": 5, "height": 5, "user": this.props.player, "id": gameId}));
  }

  render() {
    let players = [];
    let spymasterDisabled = null;
    let spymasterRedStyle = {visibility: 'hidden'};
    let spymasterBlueStyle = {visibility: 'hidden'};
    let gameStarter = false;
    for (let user of this.state.user_list) {
      let isCurrent = user === this.props.player;
      if (isCurrent && this.state.user_list.indexOf(user) === 0) {
        gameStarter = true;
      }
      if (this.state.red_team.indexOf(user) >= 0) {
        if (isCurrent) {
          spymasterRedStyle.visibility = 'visible';
        }
        spymasterDisabled = !!this.state.red_spymaster;
        players.push(<Player name={user} team="red" key={user} current={isCurrent} action={this.handleClick} disabled={this.state.disabled}></Player>)
      } else if (this.state.blue_team.indexOf(user) >= 0) {
        if (isCurrent) {
          spymasterBlueStyle.visibility = 'visible';
        }
        spymasterDisabled = !!this.state.blue_spymaster;
        players.push(<Player name={user} team="blue" key={user} current={isCurrent} action={this.handleClick} disabled={this.state.disabled}></Player>)
      } else {
        players.push(<Player name={user} key={user} current={isCurrent} action={this.handleClick} disabled={this.state.disabled}></Player>)
      }
    }
    let redColumnHeader = "Red";
    let blueColumnHeader = "Blue";
    if (this.state.red_spymaster) {
      redColumnHeader += " Spymaster: " + this.state.red_spymaster;
    }
    if (this.state.blue_spymaster) {
      blueColumnHeader += " Spymaster: " + this.state.blue_spymaster;
    }
    
    return (
      <div>
        <h4>Your Game ID: {this.props.gameId.split('-').slice(1).join(' ')}</h4>
        <div style={gameStarter? {}: {display: "none"}}><button type={"button"} className={"btn btn-primary"} onClick={this.startGame} disabled={this.state.disabled || (gameStarter && !this.readyStart())}>Start Game</button></div>
        <div className={"row"}>
          <div className={"col row d-none d-md-flex"}><div className={"col"}><button type={"button"} style={spymasterRedStyle} className={"btn btn-danger mr-2"} onClick={this.requestRedSpymaster} disabled={this.state.disabled || spymasterDisabled}>Request Spymaster</button></div><div className={"col"}>{redColumnHeader}</div></div>
          <div className={"col row d-md-none"}><div className={"col"}>{redColumnHeader}</div><div className={"col"}><button type={"button"} style={spymasterRedStyle} className={"btn btn-danger mr-2"} onClick={this.requestRedSpymaster} disabled={this.state.disabled || spymasterDisabled}>Request Spymaster</button></div></div>
          <div className={"col"}>Random</div>
          <div className={"col row"}><div className={"col"}>{blueColumnHeader}</div><div className={"col"}><button type={"button"} style={spymasterBlueStyle} className={"btn btn-primary ml-2"} onClick={this.requestBlueSpymaster} disabled={this.state.disabled || spymasterDisabled}>Request Spymaster</button></div></div>
        </div>
        <hr></hr>
        <div>
          {players}
        </div>
      </div>
    );
  }
}

class Player extends React.Component {
  constructor(props) {
    super(props);
    this.redClick = this.redClick.bind(this);
    this.blueClick = this.blueClick.bind(this);
    this.randomClick = this.randomClick.bind(this);
  }

  redClick(e) {
    this.props.action('red', false, e);
  }

  blueClick(e) {
    this.props.action('blue', false, e);
  }

  randomClick(e) {
    this.props.action('random', false, e);
  }

  render() {
    let before = null;
    let after = null;
    let cardClass = null;
    let flexClass = null;
    if (this.props.current) {
      before = [<div key={'div0'} className={'no-marg col row justify-content-center'}>
                  <button type={"button"} className={"btn btn-danger my-auto"} onClick={this.redClick} disabled={this.props.disabled}>Red Team</button>
                </div>];
      after = [<div key={'div0'} className={'no-marg col row justify-content-center'}>
                 <button type={"button"} className={"btn btn-primary my-auto"} onClick={this.blueClick} disabled={this.props.disabled}>Blue Team</button>
               </div>];
      cardClass = 'bg-light';
      flexClass = 'justify-content-center';
      if (this.props.team === "red") {
        before = [];
        after = [<div key={'div0'} className={'no-marg col row justify-content-center'}>
                   <button type={"button"} className={"btn btn-secondary my-auto"} onClick={this.randomClick} disabled={this.props.disabled}>Random Team</button>
                 </div>,
                 <div key={'div1'} className={'no-marg col row justify-content-center'}>
                   <button type={"button"} className={"btn btn-primary my-auto"} onClick={this.blueClick} disabled={this.props.disabled}>Blue Team</button>
                 </div>];
        cardClass = 'bg-danger';
        flexClass = 'justify-content-start';
      } else if (this.props.team === "blue") {
      before = [<div key={'div0'} className={'no-marg col row justify-content-center'}>
                  <button type={"button"} className={"btn btn-danger my-auto"} onClick={this.redClick} disabled={this.props.disabled}>Red Team</button>
                </div>,
                <div key={'div1'} className={'no-marg col row justify-content-center'}>
                  <button type={"button"} className={"btn btn-secondary my-auto"} onClick={this.randomClick} disabled={this.props.disabled}>Random Team</button>
                </div>];
        after = [];
        cardClass = 'bg-primary';
        flexClass = 'justify-content-end';
      }
    } else {
      before = [<div key={'div0'} className={'col'}></div>];
      after = [<div key={'div1'} className={'col'}></div>];
      cardClass = 'bg-light';
      flexClass = 'justify-content-center';
      if (this.props.team === "red") {
        before = [];
        after = [<div key={'div0'} className={'col'}></div>,<div key={'div1'} className={'col'}></div>];
        cardClass = 'bg-danger';
        flexClass = 'justify-content-start';
      } else if (this.props.team === "blue") {
      before = [<div key={'div0'} className={'col'}></div>,<div key={'div1'} className={'col'}></div>];
        after = [];
        cardClass = 'bg-primary';
        flexClass = 'justify-content-end';
      }
    }
    return (
    <div className={"row my-3"}>
      <FlipMove style={{display: "flex", width: "100%"}}>
      {before}
      <div className={"col"} key={"player"}>
        <Card cardClass={cardClass} name={this.props.name}></Card>
      </div>
      {after}
      </FlipMove> 
    </div>
    );
  }
}

$('#submit-username').click(addPlayer);

$("#username-input").keypress(function (e) {
  if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
      $('#submit-username').click();
      return false;
  } else {
      return true;
  }
});
$('#username-modal').modal({'backdrop': 'static', 'keyboard': false, 'show': false});
$('#username-modal').on('show.bs.modal', function (event) {
  setTimeout(() => $('#username-input').focus(), 850);
})
