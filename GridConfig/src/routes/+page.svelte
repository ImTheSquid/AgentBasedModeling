<script lang="ts">
	import { onMount } from 'svelte';
	import { CellType, cellTypeKeys, colorForCell, type Cell, type EntranceCell } from '$lib';
	import { SvelteSet } from 'svelte/reactivity';

	function downloadJSON() {
		// Convert the JSON data to a string
		const jsonString = JSON.stringify(
			{
				gridSize: sideLength,
				data: gridData
			},
			null,
			2
		);

		// Create a Blob from the JSON string
		const blob = new Blob([jsonString], { type: 'application/json' });

		// Create a temporary anchor element
		const link = document.createElement('a');
		link.href = URL.createObjectURL(blob);

		// Set the download attribute with a file name
		link.download = 'data.json';

		// Programmatically click the link to trigger the download
		link.click();

		// Clean up by revoking the object URL
		URL.revokeObjectURL(link.href);
	}

	function handleFileUpload(event: Event): void {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0]; // Get the uploaded file

		if (file && file.type === 'application/json') {
			const reader = new FileReader();

			// Read the file as text
			reader.onload = (e: ProgressEvent<FileReader>) => {
				try {
					if (e.target?.result) {
						// Parse the JSON content
						let parsed: { data: Record<string, Cell>; gridSize: number } = JSON.parse(
							e.target.result as string
						);
						gridData = parsed.data;
						sideLength = parsed.gridSize;
					}
				} catch (error) {
					console.error('Invalid JSON file:', error);
					alert('The uploaded file is not a valid JSON file.');
				}
			};

			// Trigger the file reading
			reader.readAsText(file);
		} else {
			alert('Please upload a valid JSON file.');
		}
	}

	function createSvg(tagName: string) {
		var svgNS = 'http://www.w3.org/2000/svg';
		return document.createElementNS(svgNS, tagName);
	}

	let grid = function (numberPerSide: number, size: number, pixelsPerSide: number) {
		let svg = createSvg('svg');
		svg.setAttribute('width', pixelsPerSide.toString());
		svg.setAttribute('height', pixelsPerSide.toString());
		svg.setAttribute('viewBox', [0, 0, numberPerSide * size, numberPerSide * size].join(' '));

		for (let i = 0; i < numberPerSide; i++) {
			for (let j = 0; j < numberPerSide; j++) {
				var number = `${j}, ${i}`;
				let cellData = number in gridData ? gridData[number] : null;
				let boxColor = selectedCells.has(number)
					? 'yellow'
					: cellData !== null
						? colorForCell(cellData.type)
						: 'white';
				let textColor = cellData !== null ? 'white' : 'black';
				let g = createSvg('g');
				g.setAttribute('transform', ['translate(', j * size, ',', i * size, ')'].join(''));
				var box = createSvg('rect');
				box.setAttribute('width', size.toString());
				box.setAttribute('height', size.toString());
				box.setAttribute('fill', boxColor);
				box.setAttribute('style', 'stroke-width:1;stroke:rgb(0,0,0);');
				box.setAttribute('id', number.toString());
				g.appendChild(box);
				if (showNumbers) {
					var text = createSvg('text');
					text.appendChild(document.createTextNode(number));
					text.setAttribute('fill', textColor);
					text.setAttribute('font-size', '3');
					text.setAttribute('x', '1');
					text.setAttribute('y', (size / 2 + 1).toString());
					text.setAttribute('id', number.toString());
					text.setAttribute('style', 'user-select: none;');
					g.appendChild(text);
				}
				svg.appendChild(g);
			}
		}
		svg.addEventListener(
			'click',
			function (e) {
				let target = e.target as HTMLElement | null;
				let id = target?.id;
				if (!id) return;

				if (cellPickMode) {
					let data = id.split(',');
					let x = Number(data[0]);
					let y = Number(data[1]);
					gridData[cellPickMode].associatedExit = [x, y];
					cellPickMode = null;
					return;
				} else if (inSelectionMode) {
					selectedCells.add(id);
					return;
				}

				// Is there already grid data for this cell?
				if (id in gridData) {
					if (gridData[id].type == cellTypeKeys.length - 1) {
						delete gridData[id];
					} else {
						gridData[id].type += 1;
						gridData[id].associatedExit = null;
					}
				} else {
					gridData[id] = {
						type: 0,
						associatedExit: [-1, -1] as [number, number]
					};
				}
			},
			false
		);
		svg.addEventListener(
			'mousemove',
			(e) => {
				let target = e.target as HTMLElement | null;
				if (!target?.id) return;
				if (inSelectionMode && activeSelect) {
					selectedCells.add(target.id);
				}
			},
			false
		);
		svg.addEventListener('mousedown', (_) => {
			console.log('mousedown');
			activeSelect = true;
		});
		svg.addEventListener('mouseup', (_) => {
			activeSelect = false;
		});
		return svg;
	};

	let gridData: Record<string, Cell> = $state({});
	let selectedCells: SvelteSet<string> = $state(new SvelteSet());
	let sideLength: number = $state(5);
	let showNumbers: boolean = $state(true);
	let inSelectionMode: boolean = $state(false);
	let activeSelect: boolean = $state(false);
	let cellPickMode: string | null = $state(null);

	$effect(() => {
		sideLength = Math.max(sideLength, 1);
		let container = document.getElementById('container') as HTMLElement;
		container.innerHTML = '';
		container.appendChild(grid(sideLength, 10, Math.max(sideLength * 50, 250)));
	});

	function clearSelection() {
		selectedCells.clear();
	}

	function setAllSelectedToType(cellType: CellType | null) {
		if (cellType === null) {
			for (let item of selectedCells) {
				delete gridData[item];
			}
		} else {
			for (let item of selectedCells) {
				if (cellType == CellType.Entrance && gridData[item]?.type != CellType.Entrance) {
					gridData[item] = {
						type: CellType.Entrance,
						associatedExit: [-1, -1] as [number, number]
					};
				} else if (cellType != CellType.Entrance) {
					gridData[item] = {
						type: cellType,
						associatedExit: null
					};
				}
			}
		}
		inSelectionMode = false;
		clearSelection();
	}
</script>

<h1 class="text-xl">HONR 313 Agent-Based Modeling Grid Configurator</h1>
<button
	class={`${inSelectionMode ? 'bg-red-300' : 'bg-gray-300'} p-2`}
	onclick={(_) => (inSelectionMode = !inSelectionMode)}>Toggle Selection</button
>
<button class="bg-gray-300 p-2" onclick={(_) => clearSelection()}>Clear Selection</button>
<button class="bg-green-300 p-2" onclick={(_) => downloadJSON()}>DOWNLOAD</button>
<input type="file" accept="application/json" onchange={handleFileUpload} />
<label for="length">Num per side:</label>
<input id="length" bind:value={sideLength} type="number" />
<label for="showNumbers">Show numbers:</label>
<input id="showNumbers" bind:checked={showNumbers} type="checkbox" />
<p>KEY:</p>
{#if inSelectionMode}
	<button class="bg-gray-300" onclick={(_) => setAllSelectedToType(null)}>CLEAR</button>
{/if}
<ul>
	{#each cellTypeKeys as k, i}
		<li style={`color: ${colorForCell(i as CellType)};`}>
			{#if inSelectionMode}
				<button class="bg-gray-300" onclick={(_) => setAllSelectedToType(i as CellType)}>{k}</button
				>
			{:else}
				{k}
			{/if}
		</li>
	{/each}
</ul>
<div id="container"></div>
{#if Object.values(gridData).filter((g) => g.type === CellType.Entrance).length > 0}
	<h2 class="text-lg font-bold">Entrance Node Associations (0 indexed)</h2>
	<ul>
		{#each Object.keys(gridData).filter((g) => gridData[g].type === CellType.Entrance) as data}
			<li>
				{data}: X:
				<input type="number" bind:value={(gridData[data] as EntranceCell).associatedExit[0]} />
				Y:
				<input type="number" bind:value={(gridData[data] as EntranceCell).associatedExit[1]} />

				<button
					class={`${cellPickMode === data ? 'bg-red-300' : 'bg-gray-300'} p-2`}
					onclick={(_) => (cellPickMode = data)}>Pick Cell</button
				>
			</li>
		{/each}
	</ul>
{/if}
